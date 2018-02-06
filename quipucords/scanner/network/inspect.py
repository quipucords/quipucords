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
from api.models import (ScanTask, ConnectionResult,
                        SystemConnectionResult)
from scanner.task import ScanTaskRunner
from scanner.network.inspect_callback import InspectResultCallback
from scanner.network.utils import (_construct_error_msg,
                                   _credential_vars,
                                   _construct_vars,
                                   run_playbook,
                                   write_inventory)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Timeout for individual tasks. Must match format in 'man timeout'.
DEFAULT_TIMEOUT = '120s'

DEFAULT_ROLES = [
    'check_dependencies',
    'connection',
    'cpu',
    'date',
    'dmi',
    'etc_release',
    'file_contents',
    'jboss_eap',
    'jboss_brms',
    'jboss_fuse_on_karaf',
    'ifconfig',
    'redhat_packages',
    'redhat_release',
    'subman',
    'uname',
    'virt',
    'virt_what',
    'host_done',
]


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

    def __init__(self, scan_job, scan_task, inspect_results):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param inspect_results: InspectionResults object used
        to store results
        """
        super().__init__(scan_job, scan_task)
        self.inspect_results = inspect_results
        self.connect_scan_task = None

    def run(self):
        """Scan target systems to collect facts.

        Attempts connections to a source using a list of credentials
        and gathers the set of successes (host/ip, credential) and
        failures (host/ip). Runs a host scan on the set of systems that are
        reachable. Collects the associated facts for the scanned systems
        """
        # pylint: disable=too-many-return-statements, too-many-locals
        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            error_message = 'Prerequisites scan task with id %d failed.' %\
                self.connect_scan_task.id
            return error_message, ScanTask.FAILED

        try:
            # Execute scan
            connected, _, completed = self.obtain_discovery_data()
            num_completed = len(completed)
            num_remaining = len(connected)
            num_total = num_remaining + num_completed

            if num_total == 0:
                msg = 'Inventory provided no reachable hosts.'
                raise ScannerException(msg)

            self.inspect_scan(connected)

            temp_facts = self.get_facts()
            fact_size = len(temp_facts)
            if temp_facts is None or fact_size == 0:
                msg = 'SystemFacts set is empty.  '\
                    'No results will be reported to fact endpoint.'
                return msg, ScanTask.FAILED

            # Clear cache as results changed
            self.result = None

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
        return None, ScanTask.COMPLETED

    # pylint: disable=too-many-locals,W0102
    def inspect_scan(self, connected, roles=DEFAULT_ROLES,
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

        extra_vars = self.scan_job.get_extra_vars()
        forks = self.scan_job.options.max_concurrency

        # Save counts
        self.scan_task.update_stats('INITIAL NETWORK INSPECT STATS',
                                    sys_count=len(connected),
                                    sys_scanned=0, sys_failed=0)

        ssh_executable = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '../../../bin/timeout_ssh'))

        base_ssh_executable = base_ssh_executable or 'ssh'
        ssh_timeout = ssh_timeout or DEFAULT_TIMEOUT
        ssh_args = ['--executable=' + base_ssh_executable,
                    '--timeout=' + ssh_timeout]

        group_names, inventory = construct_scan_inventory(
            connected, connection_port, forks,
            ssh_executable=ssh_executable,
            ssh_args=ssh_args)
        inventory_file = write_inventory(inventory)

        error_msg = ''
        for group_name in group_names:
            callback =\
                InspectResultCallback(scan_task=self.scan_task,
                                      inspect_results=self.inspect_results)
            playbook = {'name': 'scan systems for product fingerprint facts',
                        'hosts': group_name,
                        'gather_facts': False,
                        'roles': roles}
            result = run_playbook(
                inventory_file, callback, playbook,
                extra_vars, forks=forks)

            if result != TaskQueueManager.RUN_OK:
                new_error_msg = _construct_error_msg(result)
                logger.error(new_error_msg)
                error_msg += '{}\n'.format(new_error_msg)

        if error_msg != '':
            raise AnsibleError(error_msg)

        # Clear this cache since new results are available
        self.facts = None

    def obtain_discovery_data(self):
        """Obtain discover scan data.  Either via new scan or paused scan.

        :returns: List of connected, failed, and completed.
        """
        connected = []
        failed = []
        completed = []
        conn_task_results = ConnectionResult.objects.filter(
            scan_task=self.connect_scan_task.id).first()
        for result in conn_task_results.systems.all():
            if result.status == SystemConnectionResult.SUCCESS:
                host_cred = result.credential
                serializer = CredentialSerializer(host_cred)
                connected.append((result.name, serializer.data))
            elif result.status == SystemConnectionResult.FAILED:
                failed.append(result.name)

        for inspect in self.inspect_results.results.all():
            for result in inspect.systems.all():
                completed.append(result.name)
        return connected, failed, completed


# pylint: disable=too-many-locals
def construct_scan_inventory(hosts, connection_port, concurrency_count,
                             ssh_executable=None, ssh_args=None):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts/credential tuples
    :param connection_port: The connection port
    :param concurrency_count: The number of concurrent scans
    :param ssh_executable: the ssh executable to use, or None for 'ssh'
    :param ssh_args: a list of extra ssh arguments, or None
    :returns: A dictionary of the ansible inventory
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
