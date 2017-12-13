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
from ansible.parsing.splitter import parse_kv
from api.serializers import SourceSerializer, CredentialSerializer
from api.models import (Credential, ScanTask, ConnectionResults,
                        ConnectionResult, SystemConnectionResult)
from scanner import (ScanTaskRunner, ResultCallback)
from scanner.network.utils import (_handle_ssh_passphrase,
                                   run_playbook,
                                   _construct_error,
                                   _construct_vars,
                                   write_inventory)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.conn_results = None

    def _store_discovery_success(self, connected, failed_hosts):
        result = {}
        conn_result = ConnectionResult(
            scan_task=self.scan_task, source=self.scan_task.source)
        conn_result.save()

        for success in connected:
            result[success[0]] = success[1]
            # pylint: disable=no-member
            cred = Credential.objects.get(pk=success[1]['id'])
            sys_result = SystemConnectionResult(
                name=success[0], status=SystemConnectionResult.SUCCESS,
                credential=cred)
            sys_result.save()
            conn_result.systems.add(sys_result)

        for failed in failed_hosts:
            result[failed] = None
            sys_result = SystemConnectionResult(
                name=failed, status=SystemConnectionResult.FAILED)
            sys_result.save()
            conn_result.systems.add(sys_result)

        conn_result.save()
        self.conn_results.save()
        self.conn_results.results.add(conn_result)
        self.conn_results.save()

        return result

    def get_results(self):
        """Access connection results."""
        if not self.results or not self.conn_results:
            # pylint: disable=no-member
            self.conn_results = ConnectionResults.objects.filter(
                scan_job=self.scan_job.id).first()
            self.results = self.conn_results.results.filter(
                scan_task=self.scan_task.id)
        return self.results

    def run(self):
        """Scan network range ang attempt connections."""
        try:
            connected, failed_hosts = self.discovery()
            self.facts = self._store_discovery_success(connected, failed_hosts)
        except AnsibleError as ansible_error:
            logger.error('Discovery scan failed for %s. %s', self.scan_task,
                         ansible_error)
            return ScanTask.FAILED

        return ScanTask.COMPLETED

    # pylint: disable=too-many-locals
    def discovery(self):
        """Execute the discovery scan with the initialized source.

        :returns: list of connected hosts credential tuples and
                  list of host that failed connection
        """
        connected = []
        serializer = SourceSerializer(self.scan_task.source)
        source = serializer.data
        remaining = source['hosts']
        credentials = source['credentials']
        connection_port = source['ssh_port']

        logger.info('Discovery scan started for %s.', self.scan_task)

        forks = self.scan_job.options.max_concurrency
        for cred_id in credentials:
            cred_obj = Credential.objects.get(pk=cred_id)
            hc_serializer = CredentialSerializer(cred_obj)
            cred = hc_serializer.data
            connected, remaining = connect(remaining, cred, connection_port,
                                           forks=forks)

            # Update the scan counts
            if self.scan_task.systems_count is None:
                self.scan_task.systems_count = len(
                    connected) + len(remaining)
                self.scan_task.systems_scanned = 0
            self.scan_task.systems_scanned += len(connected)
            self.scan_task.save()

            if remaining == []:
                break

        logger.info('Discovery scan completed for %s.', self.scan_task)
        logger.info('Successfully connected to %d systems.', len(connected))
        if bool(remaining):
            logger.warning('Failed to connect to %d systems.', len(remaining))
            logger.debug('Failed systems: %s', remaining)

        return connected, remaining


def connect(hosts, credential, connection_port, forks=50):
    """Attempt to connect to hosts using the given credential.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param forks: number of forks to run with, default of 50
    :returns: list of connected hosts credential tuples and
            list of host that failed connection
    """
    success = []
    failed = []
    inventory = construct_connect_inventory(hosts, credential, connection_port)
    inventory_file = write_inventory(inventory)
    callback = ResultCallback()

    playbook = {'name': 'discovery play',
                'hosts': 'all',
                'gather_facts': 'no',
                'tasks': [{'action': {'module': 'raw',
                                      'args': parse_kv('echo "Hello"')}}]}

    _handle_ssh_passphrase(credential)
    result = run_playbook(inventory_file, callback, playbook, forks=forks)
    if (result != TaskQueueManager.RUN_OK and
            result != TaskQueueManager.RUN_UNREACHABLE_HOSTS):
        raise _construct_error(result)

    success, failed = _process_connect_callback(callback, credential)

    return success, failed


def _process_connect_callback(callback, credential):
    """Process the callback information from a scan.

     Create the success and failed lists from callback data.

    :param callback: The callback handler
    :param credential: The credential used for connections
    :returns: list of connected hosts credential tuples and
              list of host that failed connection
    """
    success = []
    failed = []
    if isinstance(callback, ResultCallback):
        for connection_result in callback.results:
            if 'host' in connection_result:
                host = connection_result['host']
                if 'result' in connection_result:
                    task_result = connection_result['result']
                    if 'rc' in task_result and task_result['rc'] is 0:
                        success.append((host, credential))
                    else:
                        failed.append(host)
                else:
                    failed.append(host)

    return success, failed


def construct_connect_inventory(hosts, credential, connection_port):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :returns: A dictionary of the ansible invetory
    """
    inventory = None
    hosts_dict = {}

    for host in hosts:
        hosts_dict[host] = None

    vars_dict = _construct_vars(connection_port, credential)

    inventory = {'all': {'hosts': hosts_dict, 'vars': vars_dict}}
    return inventory
