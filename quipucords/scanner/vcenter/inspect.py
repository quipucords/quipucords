"""ScanTask used for vcenter inspection task."""

import logging
from datetime import UTC, datetime
from functools import cached_property
from socket import gaierror

from django.db import transaction
from pyVmomi import vim, vmodl

from api.inspectresult.model import InspectGroup
from api.models import InspectResult, RawFact, ScanTask, SystemConnectionResult
from api.status.misc import get_server_id
from quipucords.environment import server_version
from scanner.runner import ScanTaskRunner
from scanner.vcenter.utils import (
    ClusterRawFacts,
    HostRawFacts,
    VcenterRawFacts,
    raw_facts_template,
    retrieve_properties,
    vcenter_connect,
)

logger = logging.getLogger(__name__)


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
                    if ":" not in ip_addr.ipAddress:  # Only grab ipv4 addrs
                        ip_addresses.append(ip_addr.ipAddress)
    return mac_addresses, ip_addresses


def get_vm_names(content):
    """Get the vm names from the container view.

    :param vm_container_view: The VM container view.
    :returns: list of vm names.
    """
    vm_names = []

    visit_folders = vmodl.query.PropertyCollector.TraversalSpec(
        name="visitFolders", type=vim.Folder, path="childEntity", skip=False
    )

    visit_folders.selectSet.extend(
        [
            vmodl.query.PropertyCollector.SelectionSpec(name="visitFolders"),
            vmodl.query.PropertyCollector.SelectionSpec(name="dcToVmFolder"),
        ]
    )

    dc_to_vm_folder = vmodl.query.PropertyCollector.TraversalSpec(
        name="dcToVmFolder", type=vim.Datacenter, path="vmFolder", skip=False
    )
    dc_to_vm_folder.selectSet.extend(
        [vmodl.query.PropertyCollector.SelectionSpec(name="visitFolders")]
    )

    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet=[
            vmodl.query.PropertyCollector.ObjectSpec(
                obj=content.rootFolder,
                skip=False,
                selectSet=[visit_folders, dc_to_vm_folder],
            ),
        ],
        propSet=[
            vmodl.query.PropertyCollector.PropertySpec(
                all=False,
                type=vim.VirtualMachine,
                pathSet=["name"],
            ),
        ],
    )

    objects = retrieve_properties(content, [filter_spec])
    for object_content in objects:
        vm_names.append(object_content.propSet[0].val)

    return vm_names


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner vcenter connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available virtual systems.
    """

    def execute_task(self):
        """Scan vcenter range and attempt scan."""
        message, status = self.check_connection()
        if status != ScanTask.COMPLETED:
            return message, status

        message, status = self.inspect()
        return message, status

    def check_connection(self):
        """
        Check the connection before inspecting.

        This is redundant because we could just scan immediately and handle
        its failure as needed, but this exists due to legacy design decision
        that requires an existing list of connection results to be referenced
        later during the inspection. This could (should) be flattened into a
        single operation.

        TODO Remove this function when we remove connect scan tasks.
        """
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()
        try:
            connected = self.connect()
            self._store_connect_data(connected, credential, source)
        except vim.fault.InvalidLogin as vm_error:
            error_message = (
                f"Unable to connect to VCenter source, {source.name},"
                f" with supplied credential, {credential.name}.\n"
            )
            error_message += f"Connect scan failed for {self.scan_task}. {vm_error}"
            return error_message, ScanTask.FAILED
        except gaierror as error:
            error_message = f"Unable to connect to VCenter source {source.name}.\n"
            error_message += f"Reason for failure: {error}"
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    def _store_connect_data(self, connected, credential, source):
        """Update the scan counts."""
        for system in connected:
            sys_result = SystemConnectionResult.objects.create(
                name=system,
                status=SystemConnectionResult.SUCCESS,
                credential=credential,
                source=source,
                task_connection_result=self.scan_task.connection_result,
            )
            self.scan_task.increment_stats(sys_result.name, increment_sys_scanned=True)

        self.scan_task.connection_result.save()

    def connect(self):
        """Execute the connect scan with the initialized source.

        :returns: list of connected vm credential tuples
        """
        # TODO Remove this function and store vm names as part of inspect.
        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        vm_names = get_vm_names(content)

        return vm_names

    def inspect(self):
        """Perform the actual inspect operations and progressively save results."""
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()

        try:
            self._inspect()
        except vim.fault.InvalidLogin as vm_error:
            error_message = (
                f"Unable to connect to VCenter source, {source.name}, "
                f"with supplied credential, {credential.name}.\n"
                f"Discovery scan failed for {(self.scan_task,)}. {vm_error}"
            )
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    def parse_parent_props(self, obj, props):
        """Parse Parent properties.

        :param obj: ManagedObject which we are parsing the parent for
        :param props: Array of Dynamic Properties
        """
        facts = {}
        facts["type"] = obj.__class__.__name__
        for prop in props:
            if prop.name == "name":
                facts["name"] = prop.val
            elif prop.name == "parent":
                if prop.val is not None:
                    facts["parent"] = str(prop.val)
        return facts

    def parse_cluster_props(self, props, parents_dict):
        """Parse Cluster properties.

        :param props: Array of Dynamic Properties
        :param parents_dict: Dictionary of parent properties
        """
        facts = {}
        for prop in props:
            if prop.name == "name":
                facts[ClusterRawFacts.NAME] = prop.val
            elif prop.name == "parent":
                parent = parents_dict.get(str(prop.val))
                while parent and parent.get("type") != "vim.Datacenter":
                    parent = parents_dict.get(parent.get("parent"))
                facts[ClusterRawFacts.DATACENTER] = (
                    parent.get("name") if parent else None
                )
        return facts

    def parse_host_props(self, props, cluster_dict):
        """Parse Host properties.

        :param props: Array of Dynamic Properties
        :param cluster_dict: Dictionary of cluster properties
        """
        facts = {}
        for prop in props:
            if prop.name == "parent":
                cluster_info = cluster_dict.get(str(prop.val), {})
                facts[HostRawFacts.CLUSTER] = cluster_info.get(ClusterRawFacts.NAME)
                facts[HostRawFacts.DATACENTER] = cluster_info.get(
                    ClusterRawFacts.DATACENTER
                )
            elif prop.name == "summary.config.name":
                facts[HostRawFacts.NAME] = prop.val
            elif prop.name == "hardware.systemInfo.uuid":
                facts[HostRawFacts.UUID] = prop.val
            elif prop.name == "summary.hardware.numCpuCores":
                facts[HostRawFacts.CPU_CORES] = prop.val
            elif prop.name == "summary.hardware.numCpuPkgs":
                facts[HostRawFacts.CPU_COUNT] = prop.val
            elif prop.name == "summary.hardware.numCpuThreads":
                facts[HostRawFacts.CPU_THREADS] = prop.val

        return facts

    @cached_property
    def _inspect_group(self):
        inspect_group = InspectGroup.objects.create(
            source_type=self.scan_task.source.source_type,
            source_name=self.scan_task.source.name,
            server_id=get_server_id(),
            server_version=server_version(),
            source=self.scan_task.source,
        )
        inspect_group.tasks.add(self.scan_task)
        return inspect_group

    @transaction.atomic
    def parse_vm_props(self, props, host_dict):  # noqa: PLR0912, C901
        """Parse (and store) Virtual Machine properties.

        :param props: Array of Dynamic Properties
        :param host_dict: Dictionary of host properties
        """
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        facts = raw_facts_template()
        for prop in props:
            if prop.name == "name":
                facts[VcenterRawFacts.NAME] = prop.val
            if prop.name == "guest.net":
                mac_addresses, ip_addresses = get_nics(prop.val)
                facts[VcenterRawFacts.MAC_ADDRESSES] = mac_addresses
                facts[VcenterRawFacts.IP_ADDRESSES] = ip_addresses
            elif prop.name == "summary.runtime.powerState":
                facts[VcenterRawFacts.STATE] = prop.val
                if facts[VcenterRawFacts.STATE] == "poweredOn":
                    facts[VcenterRawFacts.LAST_CHECK_IN] = now
            elif prop.name == "summary.guest.hostName":
                facts[VcenterRawFacts.DNS_NAME] = prop.val
            elif prop.name == "config.template":
                facts[VcenterRawFacts.TEMPLATE] = prop.val
            elif prop.name == "summary.config.guestFullName":
                facts[VcenterRawFacts.OS] = prop.val
            elif prop.name == "summary.config.memorySizeMB":
                facts[VcenterRawFacts.MEMORY_SIZE] = int(prop.val / 1024)
            elif prop.name == "summary.config.numCpu":
                facts[VcenterRawFacts.CPU_COUNT] = prop.val
            elif prop.name == "summary.config.uuid":
                facts[VcenterRawFacts.UUID] = prop.val
            elif prop.name == "runtime.host":
                host_facts = host_dict.get(str(prop.val))
                if host_facts:
                    facts[VcenterRawFacts.HOST_NAME] = host_facts.get(HostRawFacts.NAME)
                    facts[VcenterRawFacts.HOST_UUID] = host_facts.get(HostRawFacts.UUID)
                    facts[VcenterRawFacts.HOST_CPU_CORES] = host_facts.get(
                        HostRawFacts.CPU_CORES
                    )
                    facts[VcenterRawFacts.HOST_CPU_COUNT] = host_facts.get(
                        HostRawFacts.CPU_COUNT
                    )
                    facts[VcenterRawFacts.HOST_CPU_THREADS] = host_facts.get(
                        HostRawFacts.CPU_THREADS
                    )
                    facts[VcenterRawFacts.CLUSTER] = host_facts.get(
                        HostRawFacts.CLUSTER
                    )
                    facts[VcenterRawFacts.DATACENTER] = host_facts.get(
                        HostRawFacts.DATACENTER
                    )

        vm_name = facts[VcenterRawFacts.NAME]

        logger.debug("system %s facts=%s", vm_name, facts)

        sys_result = InspectResult.objects.create(
            name=vm_name,
            status=InspectResult.SUCCESS,
            inspect_group=self._inspect_group,
        )

        for key, val in facts.items():
            if val is not None:
                stored_fact = RawFact(name=key, value=val, inspect_result=sys_result)
                stored_fact.save()

        self.scan_task.increment_stats(vm_name, increment_sys_scanned=True)

    def retrieve_properties(self, content):  # noqa: C901
        """Retrieve properties from all VirtualMachines.

        :param content: ServiceInstanceContent from the vCenter connection
        """
        spec_set = self._filter_set(content.rootFolder)
        options = vmodl.query.PropertyCollector.RetrieveOptions()

        result = content.propertyCollector.RetrievePropertiesEx(
            specSet=spec_set, options=options
        )

        objects = []

        while result is not None:
            token = result.token
            objects.extend(result.objects)

            if token is None:
                break

            result = content.propertyCollector.ContinueRetrievePropertiesEx(token)

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
                cluster_dict[str(obj)] = self.parse_cluster_props(props, parents_dict)

        host_dict = {}
        for object_content in objects:
            obj = object_content.obj
            if isinstance(obj, vim.HostSystem):
                props = object_content.propSet
                host_dict[str(obj)] = self.parse_host_props(props, cluster_dict)

        for object_content in objects:
            obj = object_content.obj
            if isinstance(obj, vim.VirtualMachine):
                props = object_content.propSet
                self.parse_vm_props(props, host_dict)

    def _init_stats(self):
        """Initialize the scan_task stats."""
        # Save counts
        self.scan_task.update_stats(
            "INITIAL VCENTER CONNECT STATS.",
            sys_count=self.scan_task.systems_count,
        )

    def _property_set(self):
        """Define set of properties for _filter_set."""
        cluster_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.ComputeResource,
            pathSet=["name", "parent"],
        )

        dc_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.Datacenter,
            pathSet=["name", "parent"],
        )

        folder_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.Folder,
            pathSet=["name", "parent"],
        )

        host_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.HostSystem,
            pathSet=[
                "parent",
                "hardware.systemInfo.uuid",
                "summary.config.name",
                "summary.hardware.numCpuCores",
                "summary.hardware.numCpuPkgs",
                "summary.hardware.numCpuThreads",
            ],
        )

        vm_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False,
            type=vim.VirtualMachine,
            pathSet=[
                "guest.net",
                "name",
                "runtime.host",
                "config.template",
                "summary.guest.hostName",
                "summary.runtime.powerState",
                "summary.config.guestFullName",
                "summary.config.memorySizeMB",
                "summary.config.numCpu",
                "summary.config.uuid",
            ],
        )

        property_set = [
            cluster_property_spec,
            dc_property_spec,
            folder_property_spec,
            host_property_spec,
            vm_property_spec,
        ]

        return property_set

    def _filter_set(self, root_folder):
        """Create a filter set for the retrieve properties function.

        :param root_folder: root folder of the vcenter hierarchy
        """
        # Create traversal set
        folder_to_child_entity = vmodl.query.PropertyCollector.TraversalSpec(
            name="folderToChildEntity", type=vim.Folder, path="childEntity", skip=False
        )

        folder_to_child_entity.selectSet.extend(
            [
                vmodl.query.PropertyCollector.SelectionSpec(name="folderToChildEntity"),
                vmodl.query.PropertyCollector.SelectionSpec(name="dcToVmFolder"),
                vmodl.query.PropertyCollector.SelectionSpec(name="dcToHostFolder"),
                vmodl.query.PropertyCollector.SelectionSpec(name="crToHost"),
            ]
        )

        dc_to_vm_folder = vmodl.query.PropertyCollector.TraversalSpec(
            name="dcToVmFolder", type=vim.Datacenter, path="vmFolder", skip=False
        )
        dc_to_vm_folder.selectSet.extend(
            [vmodl.query.PropertyCollector.SelectionSpec(name="folderToChildEntity")]
        )

        dc_to_host_folder = vmodl.query.PropertyCollector.TraversalSpec(
            name="dcToHostFolder", type=vim.Datacenter, path="hostFolder", skip=False
        )
        dc_to_host_folder.selectSet.extend(
            [vmodl.query.PropertyCollector.SelectionSpec(name="folderToChildEntity")]
        )

        cr_to_host = vmodl.query.PropertyCollector.TraversalSpec(
            name="crToHost", type=vim.ComputeResource, path="host", skip=False
        )

        traversal_set = [
            folder_to_child_entity,
            dc_to_vm_folder,
            dc_to_host_folder,
            cr_to_host,
        ]

        # Create object set
        object_set = [
            vmodl.query.PropertyCollector.ObjectSpec(
                obj=root_folder, skip=False, selectSet=traversal_set
            )
        ]

        # Create filter set
        filter_spec = [
            vmodl.query.PropertyCollector.FilterSpec(
                objectSet=object_set, propSet=self._property_set()
            )
        ]

        return filter_spec

    def _inspect(self):
        """Execute the inspection scan with the initialized source."""
        # Save counts
        self._init_stats()
        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        self.retrieve_properties(content)
