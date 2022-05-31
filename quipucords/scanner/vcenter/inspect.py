#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for vcenter inspection task."""
import json
import logging
from datetime import datetime

from django.db import transaction
from pyVmomi import vim, vmodl  # pylint: disable=no-name-in-module

from api.models import RawFact, ScanTask, SystemInspectionResult
from scanner.task import ScanTaskRunner
from scanner.vcenter.utils import (
    ClusterRawFacts,
    HostRawFacts,
    VcenterRawFacts,
    raw_facts_template,
    vcenter_connect,
)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_nics(guest_net):
    """Get the network information for a VM.

    :param guest: The VM guest information.
    :returns: The list of mac addresses and ip ip_addresses
    """
    mac_addresses = []
    ip_addresses = []
    for nic in guest_net:
        if nic.network:  # Only return adapter backed interfaces
            if nic.ipConfig is not None and nic.ipConfig.ipAddress is not None:
                mac_addresses.append(nic.macAddress)
                ipconf = nic.ipConfig.ipAddress
                for ip_addr in ipconf:
                    if ':' not in ip_addr.ipAddress:  # Only grab ipv4 addrs
                        ip_addresses.append(ip_addr.ipAddress)
    return mac_addresses, ip_addresses


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner vcenter connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available virtual systems.
    """

    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.connect_scan_task = None
        self.source = scan_task.source

    def run(self, manager_interrupt):
        """Scan vcenter range and attempt scan."""
        # Make sure job is not cancelled or paused
        super_message, super_status = super().run(manager_interrupt)
        if super_status != ScanTask.COMPLETED:
            return super_message, super_status
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            error_message = (
                "Prerequisites scan task f'{self.connect_scan_task.sequence_number}'"
                " failed."
            )
            return error_message, ScanTask.FAILED

        try:
            self.inspect()
        except vim.fault.InvalidLogin as vm_error:  # pylint: disable=unused-argument
            error_message = (
                "Unable to connect to VCenter source, f'{source.name}', "
                "with supplied credential, f'{credential.name}'.\n"
            )
            error_message += (
                "Discovery scan failed for f'{self.scan_task,}'."
                "f'{vm_error}'"  # pylint: disable=unused-argument
            )
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    # pylint: disable=no-self-use
    def parse_parent_props(self, obj, props):
        """Parse Parent properties.

        :param obj: ManagedObject which we are parsing the parent for
        :param props: Array of Dynamic Properties
        """
        facts = {}
        facts['type'] = obj.__class__.__name__
        for prop in props:
            if prop.name == 'name':
                facts['name'] = prop.val
            elif prop.name == 'parent':
                if prop.val is not None:
                    facts['parent'] = str(prop.val)
        return facts

    # pylint: disable=no-self-use
    def parse_cluster_props(self, props, parents_dict):
        """Parse Cluster properties.

        :param props: Array of Dynamic Properties
        :param parents_dict: Dictionary of parent properties
        """
        facts = {}
        for prop in props:
            if prop.name == 'name':
                facts[ClusterRawFacts.NAME.value] = prop.val
            elif prop.name == 'parent':
                parent = parents_dict.get(str(prop.val))
                while parent and parent.get("type") != "vim.Datacenter":
                    parent = parents_dict.get(parent.get("parent"))
                facts[ClusterRawFacts.DATACENTER.value] = (
                    parent.get("name") if parent else None
                )
        return facts

    # pylint: disable=no-self-use
    def parse_host_props(self, props, cluster_dict):
        """Parse Host properties.

        :param props: Array of Dynamic Properties
        :param cluster_dict: Dictionary of cluster properties
        """
        facts = {}
        for prop in props:
            if prop.name == 'parent':
                cluster_info = cluster_dict.get(str(prop.val), {})
                facts[HostRawFacts.CLUSTER.value] = cluster_info.get(
                    ClusterRawFacts.NAME.value
                )
                facts[HostRawFacts.DATACENTER.value] = cluster_info.get(
                    ClusterRawFacts.DATACENTER.value
                )
            elif prop.name == "summary.config.name":
                facts[HostRawFacts.NAME.value] = prop.val
            elif prop.name == 'hardware.systemInfo.uuid':
                facts[HostRawFacts.UUID.value] = prop.val
            elif prop.name == 'summary.hardware.numCpuCores':
                facts[HostRawFacts.CPU_CORES.value] = prop.val
            elif prop.name == 'summary.hardware.numCpuPkgs':
                facts[HostRawFacts.CPU_COUNT.value] = prop.val
            elif prop.name == 'summary.hardware.numCpuThreads':
                facts[HostRawFacts.CPU_THREADS.value] = prop.val

        return facts

    @transaction.atomic
    # pylint: disable=too-many-branches,too-many-locals
    def parse_vm_props(self, props, host_dict):
        """Parse Virtual Machine properties.

        :param props: Array of Dynamic Properties
        :param host_dict: Dictionary of host properties
        """
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        facts = raw_facts_template()
        for prop in props:
            if prop.name == 'name':
                facts[VcenterRawFacts.NAME.value] = prop.val
            if prop.name == 'guest.net':
                mac_addresses, ip_addresses = get_nics(prop.val)
                facts[VcenterRawFacts.MAC_ADDRESSES.value] = mac_addresses
                facts[VcenterRawFacts.IP_ADDRESSES.value] = ip_addresses
            elif prop.name == 'summary.runtime.powerState':
                facts[VcenterRawFacts.STATE.value] = prop.val
                if facts[VcenterRawFacts.STATE.value] == "poweredOn":
                    facts[VcenterRawFacts.LAST_CHECK_IN.value] = now
            elif prop.name == 'summary.guest.hostName':
                facts[VcenterRawFacts.DNS_NAME.value] = prop.val
            elif prop.name == 'summary.config.guestFullName':
                facts[VcenterRawFacts.OS.value] = prop.val
            elif prop.name == 'summary.config.memorySizeMB':
                facts[VcenterRawFacts.MEMORY_SIZE.value] = int(prop.val / 1024)
            elif prop.name == 'summary.config.numCpu':
                facts[VcenterRawFacts.CPU_COUNT.value] = prop.val
            elif prop.name == 'summary.config.uuid':
                facts[VcenterRawFacts.UUID.value] = prop.val
            elif prop.name == 'runtime.host':
                host_facts = host_dict.get(str(prop.val))
                if host_facts:
                    facts[VcenterRawFacts.HOST_NAME.value] = host_facts.get(
                        HostRawFacts.NAME.value
                    )
                    facts[VcenterRawFacts.HOST_UUID.value] = host_facts.get(
                        HostRawFacts.UUID.value
                    )
                    facts[VcenterRawFacts.HOST_CPU_CORES.value] = host_facts.get(
                        HostRawFacts.CPU_CORES.value
                    )
                    facts[VcenterRawFacts.HOST_CPU_COUNT.value] = host_facts.get(
                        HostRawFacts.CPU_COUNT.value
                    )
                    facts[VcenterRawFacts.HOST_CPU_THREADS.value] = host_facts.get(
                        HostRawFacts.CPU_THREADS.value
                    )
                    facts[VcenterRawFacts.CLUSTER.value] = host_facts.get(
                        HostRawFacts.CLUSTER.value
                    )
                    facts[VcenterRawFacts.DATACENTER.value] = host_facts.get(
                        HostRawFacts.DATACENTER.value
                    )

        vm_name = facts[VcenterRawFacts.NAME.value]

        logger.debug('system %s facts=%s', vm_name, facts)

        sys_result = SystemInspectionResult(
            name=vm_name, status=SystemInspectionResult.SUCCESS,
            source=self.scan_task.source,
            task_inspection_result=self.scan_task.inspection_result)
        sys_result.save()

        for key, val in facts.items():
            if val is not None:
                final_value = json.dumps(val)
                stored_fact = RawFact(
                    name=key,
                    value=final_value,
                    system_inspection_result=sys_result)
                stored_fact.save()

        self.scan_task.increment_stats(vm_name, increment_sys_scanned=True)

    def retrieve_properties(self, content):
        """Retrieve properties from all VirtualMachines.

        :param content: ServiceInstanceContent from the vCenter connection
        """
        spec_set = self._filter_set(content.rootFolder)
        options = vmodl.query.PropertyCollector.RetrieveOptions()

        result = content.propertyCollector.RetrievePropertiesEx(
            specSet=spec_set,
            options=options
        )

        objects = []

        while result is not None:
            token = result.token
            objects.extend(result.objects)

            if token is None:
                break

            result = content.propertyCollector.ContinueRetrievePropertiesEx(
                token
            )

        parents_dict = {}
        for object_content in objects:
            obj = object_content.obj
            if isinstance(obj, (vim.Datacenter, vim.Folder)):
                props = object_content.propSet
                parents_dict[str(obj)] = self.parse_parent_props(obj, props)

        cluster_dict = {}
        for object_content in objects:
            obj = object_content.obj

            if isinstance(obj, vim.ComputeResource):
                props = object_content.propSet
                cluster_dict[str(obj)] = \
                    self.parse_cluster_props(props, parents_dict)

        host_dict = {}
        for object_content in objects:
            obj = object_content.obj
            if isinstance(obj, vim.HostSystem):
                props = object_content.propSet
                host_dict[str(obj)] = self.parse_host_props(
                    props, cluster_dict)

        for object_content in objects:
            obj = object_content.obj
            if isinstance(obj, vim.VirtualMachine):
                props = object_content.propSet
                self.parse_vm_props(props, host_dict)

    def _init_stats(self):
        """Initialize the scan_task stats."""
        # Save counts
        self.scan_task.update_stats(
            'INITIAL VCENTER CONNECT STATS.',
            sys_count=self.connect_scan_task.systems_count)

    # pylint: disable=no-self-use
    def _property_set(self):
        """Define set of properties for _filter_set."""
        cluster_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.ComputeResource,
            pathSet=['name', 'parent'],
        )

        dc_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.Datacenter,
            pathSet=['name', 'parent'],
        )

        folder_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.Folder,
            pathSet=['name', 'parent'],
        )

        host_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.HostSystem,
            pathSet=[
                'parent',
                'hardware.systemInfo.uuid',
                'summary.config.name',
                'summary.hardware.numCpuCores',
                'summary.hardware.numCpuPkgs',
                'summary.hardware.numCpuThreads',
            ],
        )

        vm_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.VirtualMachine,
            pathSet=[
                'guest.net',
                'name',
                'runtime.host',
                'summary.guest.hostName',
                'summary.runtime.powerState',
                'summary.config.guestFullName',
                'summary.config.memorySizeMB',
                'summary.config.numCpu',
                'summary.config.uuid'
            ],
        )

        property_set = [
            cluster_property_spec,
            dc_property_spec,
            folder_property_spec,
            host_property_spec,
            vm_property_spec
        ]

        return property_set

    # pylint: disable=no-self-use
    def _filter_set(self, root_folder):
        """Create a filter set for the retrieve properties function.

        :param root_folder: root folder of the vcenter hierarchy
        """
        # Create traversal set
        folder_to_child_entity = vmodl.query.PropertyCollector.TraversalSpec(
            name='folderToChildEntity',
            type=vim.Folder,
            path='childEntity',
            skip=False)

        folder_to_child_entity.selectSet.extend([
            vmodl.query.PropertyCollector.SelectionSpec(
                name='folderToChildEntity'),
            vmodl.query.PropertyCollector.SelectionSpec(
                name='dcToVmFolder'),
            vmodl.query.PropertyCollector.SelectionSpec(
                name='dcToHostFolder'),
            vmodl.query.PropertyCollector.SelectionSpec(
                name='crToHost'),
        ])

        dc_to_vm_folder = vmodl.query.PropertyCollector.TraversalSpec(
            name='dcToVmFolder',
            type=vim.Datacenter,
            path='vmFolder',
            skip=False)
        dc_to_vm_folder.selectSet.extend([
            vmodl.query.PropertyCollector.SelectionSpec(
                name='folderToChildEntity')
        ])

        dc_to_host_folder = vmodl.query.PropertyCollector.TraversalSpec(
            name='dcToHostFolder',
            type=vim.Datacenter,
            path='hostFolder',
            skip=False)
        dc_to_host_folder.selectSet.extend([
            vmodl.query.PropertyCollector.SelectionSpec(
                name='folderToChildEntity')
        ])

        cr_to_host = vmodl.query.PropertyCollector.TraversalSpec(
            name='crToHost',
            type=vim.ComputeResource,
            path='host',
            skip=False)

        traversal_set = [
            folder_to_child_entity,
            dc_to_vm_folder,
            dc_to_host_folder,
            cr_to_host,
        ]

        # Create object set
        object_set = [vmodl.query.PropertyCollector.ObjectSpec(
            obj=root_folder, skip=False, selectSet=traversal_set)]

        # Create filter set
        filter_spec = [vmodl.query.PropertyCollector.FilterSpec(
            objectSet=object_set, propSet=self._property_set())]

        return filter_spec

    # pylint: disable=too-many-locals
    def inspect(self):
        """Execute the inspection scan with the initialized source."""
        # Save counts
        self._init_stats()

        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        self.retrieve_properties(content)
