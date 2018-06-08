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

from pyVmomi import vim  # pylint: disable=no-name-in-module

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

    # pylint: disable=too-many-locals
    @transaction.atomic
    def get_vm_info(self, data_center, cluster, host, virtual_machine):
        """Get VM information.

        :param data_center: The data center name.
        :param cluster: The cluster name.
        :param host: The host server.
        :param virtual_machine: The virtual machine.
        """
        host_name = host.summary.config.name
        host_cpu_cores = host.summary.hardware.numCpuCores
        host_cpu_threads = host.summary.hardware.numCpuThreads
        host_cpu_count = host_cpu_threads // host_cpu_cores
        mac_addresses, ip_addresses = get_nics(virtual_machine.guest)
        summary = virtual_machine.summary
        config = summary.config
        vm_name = config.name
        vm_uuid = config.uuid
        vm_cpu_count = config.numCpu
        vm_os = config.guestFullName
        vm_mem = None
        if config.memorySizeMB is not None:
            vm_mem = int(config.memorySizeMB / 1024)

        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Need to obtain DNS Name
        facts = {'vm.name': vm_name,  # Name
                 'vm.state': summary.runtime.powerState,  # State
                 'vm.uuid': vm_uuid,  # UUID
                 'vm.cpu_count': vm_cpu_count,  # CPU
                 'vm.memory_size': vm_mem,  # Memory
                 'vm.os': vm_os,  # Guest OS
                 'vm.dns_name': summary.guest.hostName,  # DNS NAME
                 # Mac Addresses
                 'vm.mac_addresses': mac_addresses,
                 'vm.ip_addresses': ip_addresses,  # IP Addresses
                 'vm.host.name': host_name,  # Host Name
                 'vm.host.cpu_cores': host_cpu_cores,  # Host CPU Cores
                 'vm.host.cpu_threads': host_cpu_threads,  # Host CPU Threads
                 'vm.host.cpu_count': host_cpu_count,  # Host CPU Count
                 'vm.datacenter': data_center,  # Data Center
                 'vm.cluster': cluster}  # Cluster

        if summary.runtime.powerState == 'poweredOn':
            facts['vm.last_check_in'] = now

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

    def recurse_folder(self, folder):
        """Walk vcenter folders to discover datacenters.

        :param folder: The vcenter folder object.
        """
        children = folder.childEntity
        if children is not None:
            for child in children:  # pylint: disable=too-many-nested-blocks
                if child.__class__.__name__ == 'vim.Datacenter':
                    self.scan_task.log_message(
                        'Recurse vCenter datacenter: %s' % child.name)
                    self.recurse_datacenter(child)
                elif hasattr(child, 'childEntity'):
                    self.scan_task.log_message(
                        'Recurse vCenter folder: %s' % child.name)
                    self.recurse_folder(child)
                else:
                    self.scan_task.log_message(
                        'Not folder or datacenter: %s' % child.name)
        else:
            self.scan_task.log_message(
                'No children found for %s' % folder.name)

    def recurse_datacenter(self, data_center):
        """Walk datacenter to collect vm facts.

        :param data_center: The data center object.
        """
        # pylint: disable=too-many-nested-blocks
        data_center_name = data_center.name
        if hasattr(data_center, 'hostFolder'):
            clusters = data_center.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters
                if hasattr(cluster, 'name') and hasattr(cluster, 'host'):
                    cluster_name = cluster.name
                    # Variable to make pep8 compliance
                    hosts = cluster.host
                    # Iterate through Hosts in the Cluster
                    for host in hosts:
                        vms = host.vm
                        for virtual_machine in vms:
                            vm_name = virtual_machine.summary.config.name
                            sys_result = self.scan_task.inspection_result.\
                                systems.filter(name=vm_name).first()
                            if sys_result:
                                logger.debug('Results already captured'
                                             ' for vm_name=%s', vm_name)
                            else:
                                self.get_vm_info(data_center_name,
                                                 cluster_name,
                                                 host, virtual_machine)

    @transaction.atomic
    def _init_stats(self):
        """Initialize the scan_task stats."""
        # Save counts
        self.scan_task.update_stats(
            'INITIAL VCENTER CONNECT STATS.',
            sys_count=self.connect_scan_task.systems_count)

    # pylint: disable=too-many-locals
    def inspect(self):
        """Execute the inspection scan with the initialized source."""
        # Save counts
        self._init_stats()

        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        self.recurse_folder(content.rootFolder)
