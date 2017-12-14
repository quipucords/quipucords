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
from api.models import (ScanTask, InspectionResults, InspectionResult,
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


def vmsummary(summary, guest):
    """Extract VM summary data.

    :param summary: The VM summary object.
    :param guest: The VM guest object.
    :returns: Dictionary of vm summary info.
    """
    vmsum = {}
    config = summary.config
    mac_addresses, ip_addresses = get_nics(guest)
    vmsum['uuid'] = config.uuid
    vmsum['mem'] = None
    if config.memorySizeMB is not None:
        vmsum['mem'] = str(config.memorySizeMB / 1024)
    vmsum['cpu'] = str(config.numCpu)
    vmsum['ostype'] = config.guestFullName
    vmsum['state'] = summary.runtime.powerState
    vmsum['mac'] = ';'.join(mac_addresses)
    vmsum['ip_address'] = ';'.join(ip_addresses)
    vmsum['hostname'] = summary.guest.hostName

    return vmsum


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

    def get_results(self):
        """Access connection results."""
        if not self.results or not self.inspect_results:
            # pylint: disable=no-member
            self.inspect_results = InspectionResults.objects.filter(
                scan_job=self.scan_job.id).first()
            self.results = self.inspect_results.results.filter(
                scan_task=self.scan_task.id)
        return self.results

    def run(self):
        """Scan network range ang attempt connections."""
        try:
            self.inspect()
            source = self.scan_task.source
            credential = self.scan_task.source.credentials.all().first()
        except vim.fault.InvalidLogin as vm_error:
            logger.error('Unable to connect to VCenter source, %s, '
                         'with supplied credential, %s.',
                         source.name, credential.name)
            logger.error('Discovery scan failed for %s. %s', self.scan_task,
                         vm_error)
            return ScanTask.FAILED

        return ScanTask.COMPLETED

    def get_vm_info(self, data_center, cluster, host, virtual_machine):
        """Get VM information.

        :param data_center: The data center name.
        :param cluster: The cluster name.
        :param host: The host server.
        :param virtual_machine: The virtual machine.
        """
        vm_name = virtual_machine.summary.config.name
        summary = vmsummary(virtual_machine.summary,
                            virtual_machine.guest)

        # Need to obtain "DNS Name"
        facts = {'vm.name': vm_name,  # "Name"
                 'vm.state': summary['state'],  # "State"
                 'vm.uuid': summary['uuid'],  # "UUID"
                 'vm.cpu_count': summary['cpu'],  # "CPU"
                 'vm.memory_size': summary['mem'],  # "Memory"
                 'vm.os': summary['ostype'],  # "Guest OS"
                 'vm.dns_name': summary['hostname'],  # "DNS NAME"
                 'vm.mac_address': summary['mac'],  # "Mac Address"
                 'vm.ip_address': summary['ip_address'],  # "IP Address"
                 'vm.host': host,  # "Host"
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
        inspect_result = self.inspect_results.results.filter(
            source__id=self.scan_task.source.id).first()
        if inspect_result is None:
            inspect_result = InspectionResult(source=self.scan_task.source)
            inspect_result.save()
        inspect_result.systems.add(sys_result)
        inspect_result.save()
        self.inspect_results.results.add(inspect_result)
        self.inspect_results.save()

    # pylint: disable=too-many-locals
    def inspect(self):
        """Execute the inspection scan with the initialized source."""
        logger.info('Inspect scan started for %s.', self.scan_task)
        vcenter = vcenter_connect(self.scan_task)

        content = vcenter.RetrieveContent()
        children = content.rootFolder.childEntity
        for child in children:  # Iterate though DataCenters
            data_center = child
            data_center_name = data_center.name
            clusters = data_center.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in the DC
                cluster_name = cluster.name
                hosts = cluster.host  # Variable to make pep8 compliance
                for host in hosts:  # Iterate through Hosts in the Cluster
                    hostname = host.summary.config.name
                    vms = host.vm
                    for virtual_machine in vms:
                        self.get_vm_info(data_center_name, cluster_name,
                                         hostname, virtual_machine)

        logger.info('Inspect scan completed for %s.', self.scan_task)
