#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for vcenter inspection task."""
import logging
from pyVmomi import vim  # pylint: disable=no-name-in-module
from api.models import (ScanTask, InspectionResult,
                        SystemInspectionResult, RawFact)
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

    def __init__(self, scan_job, scan_task, inspect_results):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.inspect_results = inspect_results
        self.connect_scan_task = None

    def get_results(self):
        """Access connection results."""
        if not self.results or not self.inspect_results:
            self.results = InspectionResult.objects.filter(
                scan_task=self.scan_task.id).first()
        return self.results

    def run(self):
        """Scan network range ang attempt connections."""
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            logger.error(
                'Prerequisites scan task with id %d failed.',
                self.connect_scan_task.id)
            return ScanTask.FAILED

        try:
            self.inspect()
        except vim.fault.InvalidLogin as vm_error:
            logger.error('Unable to connect to VCenter source, %s, '
                         'with supplied credential, %s.',
                         source.name, credential.name)
            logger.error('Discovery scan failed for %s. %s', self.scan_task,
                         vm_error)
            return ScanTask.FAILED

        return ScanTask.COMPLETED

    # pylint: disable=too-many-locals
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

        # Need to obtain "DNS Name"
        facts = {'vm.name': vm_name,  # "Name"
                 'vm.state': summary.runtime.powerState,  # "State"
                 'vm.uuid': vm_uuid,  # "UUID"
                 'vm.cpu_count': vm_cpu_count,  # "CPU"
                 'vm.memory_size': vm_mem,  # "Memory"
                 'vm.os': vm_os,  # "Guest OS"
                 'vm.dns_name': summary.guest.hostName,  # "DNS NAME"
                 'vm.mac_address': ';'.join(mac_addresses),  # "Mac Address"
                 'vm.ip_address': ';'.join(ip_addresses),  # "IP Address"
                 'vm.host.name': host_name,  # "Host Name"
                 'vm.host.cpu_cores': host_cpu_cores,  # "Host CPU Cores"
                 'vm.host.cpu_threads': host_cpu_threads,  # "Host CPU Threads"
                 'vm.host.cpu_count': host_cpu_count,  # "Host CPU Count"
                 'vm.datacenter': data_center,  # "Data Center"
                 'vm.cluster': cluster}  # "Cluster"

        logger.debug('system %s facts=%s', vm_name, facts)

        sys_result = SystemInspectionResult(
            name=vm_name, status=SystemInspectionResult.SUCCESS)
        sys_result.save()
        for key, val in facts.items():
            if val is not None:
                stored_fact = RawFact(name=key, value=val)
                stored_fact.save()
                sys_result.facts.add(stored_fact)
        sys_result.save()

        self.inspect_results.save()
        inspect_result = InspectionResult.objects.filter(
            scan_task=self.scan_task.id).first()
        if inspect_result is None:
            inspect_result = InspectionResult(source=self.scan_task.source,
                                              scan_task=self.scan_task)
            inspect_result.save()
        inspect_result.systems.add(sys_result)
        inspect_result.save()
        self.inspect_results.results.add(inspect_result)
        self.inspect_results.save()

        self.scan_task.systems_scanned += 1
        self.scan_task.save()

    def recurse_datacenter(self, vcenter):
        """Walk datacenter to collect vm facts.

        :param vcenter: The vcenter object.
        """
        content = vcenter.RetrieveContent()
        children = content.rootFolder.childEntity
        for child in children:  # Iterate though DataCenters
            data_center = child
            data_center_name = data_center.name
            if hasattr(data_center, 'hostFolder'):
                clusters = data_center.hostFolder.childEntity
                for cluster in clusters:  # Iterate through the clusters
                    cluster_name = cluster.name
                    hosts = cluster.host  # Variable to make pep8 compliance
                    for host in hosts:  # Iterate through Hosts in the Cluster
                        vms = host.vm
                        for virtual_machine in vms:
                            self.get_vm_info(data_center_name, cluster_name,
                                             host, virtual_machine)

    # pylint: disable=too-many-locals
    def inspect(self):
        """Execute the inspection scan with the initialized source."""
        logger.info('Inspect scan started for %s.', self.scan_task)

        # Save counts
        self.scan_task.systems_count = self.connect_scan_task.systems_count
        self.scan_task.systems_scanned = 0
        self.scan_task.systems_failed = 0
        self.scan_task.save()

        vcenter = vcenter_connect(self.scan_task)
        self.recurse_datacenter(vcenter)
        logger.info('Inspect scan completed for %s.', self.scan_task)
