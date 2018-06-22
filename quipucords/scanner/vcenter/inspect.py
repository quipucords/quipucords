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

from api.models import (RawFact,
                        ScanJob,
                        ScanTask,
                        SystemInspectionResult)

from django.db import transaction

from pyVmomi import vim, vmodl  # pylint: disable=no-name-in-module

from scanner.task import ScanTaskRunner
from scanner.vcenter.utils import vcenter_connect

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_nics(guest):
    """Get the network information for a VM.

    :param guest: The VM guest information.
    :returns: The list of mac addresses and ip ip_addresses
    """
    mac_addresses = []
    ip_addresses = []
    for nic in guest.net:
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
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan canceled for %s.' % self.source.name
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.CANCELED

        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan paused for %s.' % self.source.name
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.PAUSED
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            error_message = 'Prerequisites scan task with id %d failed.' %\
                self.connect_scan_task.id
            return error_message, ScanTask.FAILED

        try:
            self.inspect()
        except vim.fault.InvalidLogin as vm_error:
            error_message = 'Unable to connect to VCenter source, %s, '\
                'with supplied credential, %s.\n' %\
                (source.name, credential.name)
            error_message += 'Discovery scan failed for %s. %s' %\
                (self.scan_task, vm_error)
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    @transaction.atomic
    def parse_vm_props(self, props):
        """Parse Virtual Machine properties

        :param props: Array of Dynamic Properties
        """

        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        facts = {}
        for prop in props:
            if prop.name == 'name':
                facts['vm.name'] = prop.val
            elif prop.name == 'summary.runtime.powerState':
                facts['vm.state'] = prop.val
                if facts['vm.state'] == 'poweredOn':
                    facts['vm.last_check_in'] = now
            elif prop.name == "summary.config.guestFullName":
                facts['vm.os'] = prop.val
            elif prop.name == "summary.config.memorySizeMB":
                facts['vm.memory_size'] = prop.val / 1024
            elif prop.name == 'summary.config.numCpu':
                facts['vm.cpu_count'] = prop.val
            elif prop.name == 'summary.config.uuid':
                facts['vm.uuid'] = prop.val

        vm_name = facts['vm.name']

        logger.debug('system %s facts=%s', vm_name, facts)

        sys_result = SystemInspectionResult(
            name=vm_name, status=SystemInspectionResult.SUCCESS,
            source=self.scan_task.source)
        sys_result.save()
        for key, val in facts.items():
            if val is not None:
                final_value = json.dumps(val)
                stored_fact = RawFact(name=key, value=final_value)
                stored_fact.save()
                sys_result.facts.add(stored_fact)
        sys_result.save()

        self.scan_task.inspection_result.systems.add(sys_result)
        self.scan_task.inspection_result.save()

        self.scan_task.increment_stats(vm_name, increment_sys_scanned=True)

    @transaction.atomic
    def retrieve_properties(self, content):
        """Retrieve properties from all VirtualMachines

        :param content: ServiceInstanceContent from the vCenter connection
        """
        spec_set = self._filter_set(content.rootFolder)
        options = vmodl.query.PropertyCollector.RetrieveOptions()

        result = content.propertyCollector.RetrievePropertiesEx(specSet=spec_set, options=options)
        while result is not None:
            objects = result.objects
            for object_content in objects:
                obj = object_content.obj
                props = object_content.propSet

                if obj.__class__.__name__ == 'vim.VirtualMachine':
                    self.parse_vm_props(props)

            if result.token is None:
                break

            result = content.propertyCollector.ContinueRetrievePropertiesEx(result.token)

    @transaction.atomic
    def _init_stats(self):
        """Initialize the scan_task stats."""
        # Save counts
        self.scan_task.update_stats(
            'INITIAL VCENTER CONNECT STATS.',
            sys_count=self.connect_scan_task.systems_count)

    def _traversal_set(self):
        folderToChildEntity = vmodl.query.PropertyCollector.TraversalSpec(
            name='folderToChildEntity', type=vim.Folder, path='childEntity', skip=False)

        folderToChildEntity.selectSet.extend([
            vmodl.query.PropertyCollector.SelectionSpec(name='folderToChildEntity'),
            vmodl.query.PropertyCollector.SelectionSpec(name='dcToVmFolder')])

        dcToVmFolder = vmodl.query.PropertyCollector.TraversalSpec(
            name='dcToVmFolder', type=vim.Datacenter, path='vmFolder', skip=False)
        dcToVmFolder.selectSet.extend([
            vmodl.query.PropertyCollector.SelectionSpec(name='folderToChildEntity')])

        return [folderToChildEntity, dcToVmFolder]

    def _object_set(self, root_folder):
        object_spec = vmodl.query.PropertyCollector.ObjectSpec(
            obj=root_folder, skip=False, selectSet=self._traversal_set())

        return [object_spec]

    def _property_set(self):
        vm_path_set = [
            "name",
            "summary.runtime.powerState",
            "summary.config.guestFullName",
            "summary.config.memorySizeMB",
            "summary.config.numCpu",
            "summary.config.uuid"
        ]

        vm_property_spec = vmodl.query.PropertyCollector.PropertySpec(
            all=False, pathSet=vm_path_set, type=vim.VirtualMachine)

        return [vm_property_spec]

    def _filter_set(self, root_folder):
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=self._object_set(root_folder),
            propSet=self._property_set())

        return [filter_spec]

    # pylint: disable=too-many-locals
    def inspect(self):
        """Execute the inspection scan with the initialized source."""
        # Save counts
        self._init_stats()

        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        self.retrieve_properties(content)
