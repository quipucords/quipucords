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
"""ScanTask used for network connection discovery."""
import logging
import os.path

from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager

from api.credential.serializer import CredentialSerializer
from api.models import (ScanJob,
                        ScanOptions,
                        ScanTask,
                        SystemConnectionResult,
                        SystemInspectionResult)

from scanner.network.inspect_callback import InspectResultCallback
from scanner.network.utils import (_construct_error_msg,
                                   _construct_vars,
                                   _credential_vars,
                                   run_playbook,
                                   write_inventory)
from scanner.task import ScanTaskRunner


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Timeout for individual tasks. Must match format in 'man timeout'.
DEFAULT_TIMEOUT = '120s'

DEFAULT_ROLES = [
    'check_dependencies',
    'connection',
    'virt',
    'cpu',
    'date',
    'dmi',
    'etc_release',
    'file_contents',
    'jboss_eap',
    'jboss_eap5',
    'jboss_brms',
    'jboss_fuse',
    'jboss_fuse_on_karaf',
    'ifconfig',
    'redhat_packages',
    'redhat_release',
    'subman',
    'uname',
    'virt_what',
    'host_done',
]

DEFAULT_SCAN_DIRS = ['/', '/opt', '/app', '/home', '/usr']
NETWORK_SCAN_IDENTITY_KEY = 'connection_host'


class ScannerException(Exception):
    """Exception for issues detected during scans."""

    def __init__(self, message=''):
        """Exception for issues detected during scans.

        :param message: An error message describing the problem encountered
        during scan.
        """
        self.message = 'Scan task failed.  Error: {}'.format(message)
        super().__init__(self.message)


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        to store results
        """
        super().__init__(scan_job, scan_task)
        self.connect_scan_task = None

    def run(self, manager_interrupt):
        """Scan target systems to collect facts.

        Attempts connections to a source using a list of credentials
        and gathers the set of successes (host/ip, credential) and
        failures (host/ip). Runs a host scan on the set of systems that are
        reachable. Collects the associated facts for the scanned systems
        """
        # pylint: disable=too-many-return-statements, too-many-locals
        # Make sure job is not cancelled or paused
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan canceled'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.CANCELED

        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan paused'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.PAUSED

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            error_message = 'Prerequisites scan task with id %d failed.' %\
                self.connect_scan_task.id
            return error_message, ScanTask.FAILED

        try:
            # Execute scan
            connected, \
                completed, \
                failed, \
                unreachable = self._obtain_discovery_data()
            processed_hosts = failed + completed
            num_total = len(connected) + len(processed_hosts)

            if num_total == 0:
                msg = 'Inventory provided no reachable hosts.'
                raise ScannerException(msg)

            self.scan_task.update_stats('INITIAL NETWORK INSPECT STATS',
                                        sys_count=len(connected),
                                        sys_scanned=len(completed),
                                        sys_failed=len(failed),
                                        sys_unreachable=len(unreachable))

            # remove completed hosts
            remaining = [
                unprocessed for unprocessed in connected
                if unprocessed[0] not in processed_hosts]
            scan_message, scan_result = self._inspect_scan(remaining)

            self.scan_task.cleanup_facts(NETWORK_SCAN_IDENTITY_KEY)
            temp_facts = self.scan_task.get_facts()
            fact_size = len(temp_facts)
            self._add_unreachable_hosts(temp_facts)
            if temp_facts is None or fact_size == 0:
                msg = 'SystemFacts set is empty.  '\
                    'No results will be reported to fact endpoint.'
                return msg, ScanTask.FAILED

        except AnsibleError as ansible_error:
            error_message = 'Scan task encountered error: %s' % \
                ansible_error
            return error_message, ScanTask.FAILED
        except AssertionError as assertion_error:
            error_message = 'Scan task encountered error: %s' % \
                assertion_error
            return error_message, ScanTask.FAILED
        except ScannerException as scan_error:
            error_message = 'Scan task encountered error: %s' % \
                scan_error
            return error_message, ScanTask.FAILED

        if self.scan_task.systems_failed > 0:
            return '%d systems could not be scanned.' % \
                self.scan_task.systems_failed, ScanTask.FAILED
        return scan_message, scan_result

    def _add_unreachable_hosts(self, systems_list):
        """Add entry for systems that were unreachable.

        :param systems_list: Current list of system results.
        """
        connected_hosts = \
            self.connect_scan_task.connection_result.systems.filter(
                status=SystemConnectionResult.SUCCESS).values('name')
        connected_hosts = set([system.get('name')
                               for system in connected_hosts])
        scanned_hosts = set([system.get(NETWORK_SCAN_IDENTITY_KEY)
                             for system in systems_list])
        unreachable_hosts = connected_hosts - scanned_hosts

        for host in unreachable_hosts:
            sys_result = SystemInspectionResult(
                name=host,
                status=SystemInspectionResult.UNREACHABLE,
                source=self.scan_task.source)
            sys_result.save()
            self.scan_task.inspection_result.systems.add(sys_result)
            self.scan_task.inspection_result.save()

    # pylint: disable=too-many-locals,W0102
    def _inspect_scan(self, connected, roles=DEFAULT_ROLES,
                      base_ssh_executable=None,
                      ssh_timeout=None):
        """Execute the host scan with the initialized source.

        :param connected: list of (host, credential) pairs to inspect
        :param roles: list of roles to execute
        :param base_ssh_executable: ssh executable, or None for
            'ssh'. Will be wrapped with a timeout before being passed
            to Ansible.
        :param ssh_timeout: string in the format of the 'timeout'
            command. Timeout for individual tasks.
        :returns: An array of dictionaries of facts

        """
        playbook = {'name': 'scan systems for product fingerprint facts',
                    'hosts': 'all',
                    'gather_facts': False,
                    'strategy': 'free',
                    'roles': roles}
        connection_port = self.scan_task.source.port

        use_paramiko = False
        if self.scan_task.source.options is not None:
            use_paramiko = self.scan_task.source.options.use_paramiko

        if self.scan_job.options is not None:
            forks = self.scan_job.options.max_concurrency
            extra_vars = self.scan_job.options.get_extra_vars()
        else:
            forks = ScanOptions.get_default_forks()
            extra_vars = ScanOptions.get_default_extra_vars()

        if extra_vars.get(ScanOptions.EXT_PRODUCT_SEARCH_DIRS) is None:
            extra_vars[ScanOptions.EXT_PRODUCT_SEARCH_DIRS] = \
                ' '.join(DEFAULT_SCAN_DIRS)

        ssh_executable = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '../../../bin/timeout_ssh'))

        base_ssh_executable = base_ssh_executable or 'ssh'
        ssh_timeout = ssh_timeout or DEFAULT_TIMEOUT

        # pylint: disable=line-too-long
        # the ssh arg is required for become-pass because
        # ansible checks for an exact string match of ssh
        # anywhere in the command array
        # See https://github.com/ansible/ansible/blob/stable-2.3/lib/ansible/plugins/connection/ssh.py#L490-L500 # noqa
        # timeout_ssh will remove the ssh argument before running the command
        ssh_args = ['--executable=' + base_ssh_executable,
                    '--timeout=' + ssh_timeout,
                    'ssh']

        group_names, inventory = _construct_scan_inventory(
            connected, connection_port, forks,
            ssh_executable=ssh_executable,
            ssh_args=ssh_args)
        inventory_file = write_inventory(inventory)

        error_msg = ''
        scan_method = 'paramiko' if use_paramiko else 'openssh'
        log_message = 'START PROCESSING GROUPS ' \
            'with %s connection configuration using ' \
            '%d forks and extra_vars=%s' % (scan_method, forks, extra_vars)
        self.scan_task.log_message(log_message)
        scan_result = ScanTask.COMPLETED
        scan_message = 'success'
        for idx, group_name in enumerate(group_names):
            log_message = 'START PROCESSING GROUP %d of %d' % (
                (idx + 1), len(group_names))
            self.scan_task.log_message(log_message)
            callback =\
                InspectResultCallback(
                    scan_task=self.scan_task)
            playbook = {'name': 'scan systems for product fingerprint facts',
                        'hosts': group_name,
                        'gather_facts': False,
                        'roles': roles}
            result = run_playbook(
                inventory_file, callback, playbook,
                extra_vars, use_paramiko, forks=forks)

            if result != TaskQueueManager.RUN_OK:
                new_error_msg = _construct_error_msg(result)
                callback.finalize_failed_hosts()
                if result != TaskQueueManager.RUN_UNREACHABLE_HOSTS and \
                        result != TaskQueueManager.RUN_FAILED_HOSTS:
                    error_msg += '{}\n'.format(new_error_msg)

        if error_msg != '':
            raise AnsibleError(error_msg)

        return scan_message, scan_result

    def _obtain_discovery_data(self):
        """Obtain discover scan data.  Either via new scan or paused scan.

        :returns: List of connected, inspection failed, and
        inspection completed.
        """
        connected = []
        failed = []
        completed = []
        unreachable = []
        nostatus = []
        for result in self.connect_scan_task.connection_result.systems.all():
            if result.status == SystemConnectionResult.SUCCESS:
                host_cred = result.credential
                serializer = CredentialSerializer(host_cred)
                connected.append((result.name, serializer.data))

        for result in self.scan_task.inspection_result.systems.all():
            if result.status == SystemInspectionResult.SUCCESS:
                completed.append(result.name)
            elif result.status == SystemInspectionResult.FAILED:
                failed.append(result.name)
            elif result.status == SystemInspectionResult.UNREACHABLE:
                unreachable.append(result.name)
            else:
                nostatus.append(result.name)

        if bool(nostatus):
            invalid_state_msg = 'Results without a validate state: %s' % (
                ', '.join(nostatus))
            self.scan_task.log_message(
                invalid_state_msg, log_level=logging.ERROR)

        return connected, completed, failed, unreachable


# pylint: disable=too-many-locals
def _construct_scan_inventory(hosts, connection_port, concurrency_count,
                              ssh_executable=None, ssh_args=None):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts/credential tuples
    :param connection_port: The connection port
    :param concurrency_count: The number of concurrent scans
    :param ssh_executable: the ssh executable to use, or None for 'ssh'
    :param ssh_args: a list of extra ssh arguments, or None
    :returns: A list of group names and a dict of the
    ansible inventory
    """
    concurreny_groups = list(
        [hosts[i:i + concurrency_count] for i in range(0,
                                                       len(hosts),
                                                       concurrency_count)])

    vars_dict = _construct_vars(connection_port)
    children = {}
    inventory = {'all': {'children': children, 'vars': vars_dict}}
    i = 0
    group_names = []
    for concurreny_group in concurreny_groups:
        hosts_dict = {}
        for host in concurreny_group:
            host_vars = _credential_vars(host[1])
            host_vars['ansible_host'] = host[0]
            if ssh_executable:
                host_vars['ansible_ssh_executable'] = ssh_executable
            if ssh_args:
                host_vars['ansible_ssh_common_args'] = ' '.join(ssh_args)
            hosts_dict[host[0]] = host_vars

        group_name = 'group_{}'.format(i)
        i += 1
        group_names.append(group_name)
        children[group_name] = {'hosts': hosts_dict}

    return group_names, inventory
