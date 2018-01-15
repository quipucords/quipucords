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
"""ScanTask used for network connection discovery."""
import logging
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
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
        logger.info('Inspect scan task started for task: %s.',
                    self.scan_task.id)

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            logger.error(
                'Prerequisites scan task with id %d failed.',
                self.connect_scan_task.id)
            return ScanTask.FAILED

        try:
            # Execute scan
            self.inspect_scan()

            # Send temp_facts to fact endpoint
            temp_facts = self.get_facts()
            fact_size = len(temp_facts)
            if temp_facts is None or fact_size == 0:
                msg = 'SystemFacts set is empty.  '\
                    'No results will be reported to fact endpoint.'
                logger.error(msg)
                return ScanTask.FAILED

            # Clear cache as results changed
            self.result = None

            logger.info('Inspect scan task %s completed.',
                        self.scan_task.id)
        except AnsibleError as ansible_error:
            logger.error(ansible_error)
            return ScanTask.FAILED
        except AssertionError as assertion_error:
            logger.error(assertion_error)
            return ScanTask.FAILED
        except ScannerException as scan_error:
            logger.error(scan_error)
            return ScanTask.FAILED

        return ScanTask.COMPLETED

    # pylint: disable=too-many-locals
    def inspect_scan(self):
        """Execute the host scan with the initialized source.

        :returns: An array of dictionaries of facts
        """
        roles = [
            'check_dependencies',
            'connection',
            'cpu',
            'date',
            'dmi',
            'etc_release',
            'file_contents',
            'jboss_eap',
            'jboss_brms',
            'ifconfig',
            'redhat_release',
            'subman',
            'uname',
            'virt',
            'virt_what',
            'host_done',
        ]
        playbook = {'name': 'scan systems for product fingerprint facts',
                    'hosts': 'all',
                    'gather_facts': False,
                    'strategy': 'free',
                    'roles': roles}
        connection_port = self.scan_task.source.port

        connected, failed, completed = self.obtain_discovery_data()
        forks = self.scan_job.options.max_concurrency

        num_completed = len(completed)
        num_remaining = len(connected)
        num_total = num_remaining + num_completed
        num_failed = len(failed)

        if num_total == 0:
            msg = 'Inventory provided no reachable hosts.'
            raise ScannerException(msg)

        logger.info('Inspect scan task started for %s.',
                    self.scan_task)
        log_msg = '%d total connected, %d completed, %d'\
            ' remaining, and make %d failed hosts'
        logger.info(log_msg,
                    num_total, num_completed, num_remaining, num_failed)

        # Save counts
        self.scan_task.systems_count = len(connected)
        self.scan_task.systems_scanned = 0
        self.scan_task.systems_failed = 0
        self.scan_task.save()

        group_names, inventory = construct_scan_inventory(
            connected, connection_port, forks)
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
                inventory_file, callback, playbook, forks=forks)

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
                credential = {'name': host_cred.name,
                              'username': host_cred.username,
                              'password': host_cred.password,
                              'sudo_password': host_cred.sudo_password,
                              'ssh_keyfile': host_cred.ssh_keyfile,
                              'ssh_passphrase':
                              host_cred.ssh_passphrase}
                connected.append((result.name, credential))
            elif result.status == SystemConnectionResult.FAILED:
                failed.append(result.name)

        for inspect in self.inspect_results.results.all():
            for result in inspect.systems.all():
                completed.append(result.name)
        return connected, failed, completed


def construct_scan_inventory(hosts, connection_port, concurrency_count):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts/credential tuples
    :param connection_port: The connection port
    :param concurrency_count: The number of concurrent scans
    :returns: A dictionary of the ansible invetory
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
            hosts_dict[host[0]] = host_vars

        group_name = 'group_{}'.format(i)
        i += 1
        group_names.append(group_name)
        children[group_name] = {'hosts': hosts_dict}

    return group_names, inventory
