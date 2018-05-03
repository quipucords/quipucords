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

from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.splitter import parse_kv

from api.models import (Credential,
                        ScanJob,
                        ScanOptions,
                        ScanTask,
                        SystemConnectionResult)
from api.serializers import CredentialSerializer, SourceSerializer

from django.db import transaction

import pexpect


from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import (_construct_error,
                                   _construct_vars,
                                   decrypt_data_as_unicode,
                                   expand_hostpattern,
                                   run_playbook,
                                   write_inventory)
from scanner.task import ScanTaskRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


# The ConnectTaskRunner creates a new ConnectResultCallback for each
# credential it tries to connect with, and the ConnectResultCallbacks
# all forward their information to a single ConnectResultStore.
class ConnectResultStore(object):
    """This object knows how to record and retrieve connection results."""

    def __init__(self, scan_task):
        """Initialize ConnectResultStore object."""
        self.scan_task = scan_task

        source = scan_task.source

        # Sources can contain patterns that describe multiple hosts,
        # like '1.2.3.[4:6]'. Expand the patterns so hosts is a list
        # of single hosts we can try to connect to.
        hosts = []
        hosts_list = source.get_hosts()
        for host in hosts_list:
            hosts.extend(expand_hostpattern(host))
        self._remaining_hosts = set(hosts)

        scan_task.update_stats('INITIAL NETWORK CONNECT STATS.',
                               sys_count=len(hosts), sys_scanned=0,
                               sys_failed=0,
                               sys_unreachable=0)

    @transaction.atomic
    def record_result(self, name, source, credential, status):
        """Record a new result, either a connection success or a failure."""
        sys_result = SystemConnectionResult(
            name=name,
            source=source,
            credential=credential,
            status=status)
        sys_result.save()

        self.scan_task.connection_result.systems.add(sys_result)
        self.scan_task.connection_result.save()

        if status == SystemConnectionResult.SUCCESS:
            message = '%s with %s' % (name, credential.name)
            self.scan_task.increment_stats(message,
                                           increment_sys_scanned=True,
                                           prefix='CONNECTED')
        elif status == SystemConnectionResult.UNREACHABLE:
            message = '%s is UNREACHABLE' % (name)
            self.scan_task.increment_stats(
                message,
                increment_sys_unreachable=True,
                prefix='FAILED')
        else:
            if credential is not None:
                message = '%s with %s' % (name, credential.name)
            else:
                message = '%s has no valid credentials' % name

            self.scan_task.increment_stats(message,
                                           increment_sys_failed=True,
                                           prefix='FAILED')

        self._remaining_hosts.remove(name)

    def remaining_hosts(self):
        """Get the set of hosts that are left to scan."""
        # Need to return a list becuase the caller can iterate over
        # our return value and call record_result repeatedly. If we
        # returned the actual list, then they would get a 'set changed
        # size during iteration' error.
        return list(self._remaining_hosts)


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
        to store results
        """
        super().__init__(scan_job, scan_task)
        self.scan_task = scan_task

    def run(self, manager_interrupt):
        """Scan network range and attempt connections."""
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

        result_store = ConnectResultStore(self.scan_task)
        return self.run_with_result_store(result_store)

    # pylint: disable=too-many-locals
    def run_with_result_store(self, result_store):
        """Run with a given ConnectResultStore."""
        serializer = SourceSerializer(self.scan_task.source)
        source = serializer.data

        if self.scan_job.options is None:
            forks = ScanOptions.get_default_forks()
        else:
            forks = self.scan_job.options.max_concurrency
        connection_port = source['port']
        credentials = source['credentials']

        remaining_hosts = result_store.remaining_hosts()

        for cred_id in credentials:
            credential = Credential.objects.get(pk=cred_id)
            if not remaining_hosts:
                message = 'Skipping credential %s.  No remaining hosts.' % \
                    credential.name
                self.scan_task.log_message(message)
                break

            message = 'Attempting credential %s.' % credential.name
            self.scan_task.log_message(message)

            cred_data = CredentialSerializer(credential).data
            callback = ConnectResultCallback(result_store, credential,
                                             self.scan_task.source)
            try:
                connect(remaining_hosts, callback, cred_data,
                        connection_port, forks=forks)
            except AnsibleError as ansible_error:
                remaining_hosts_str = ', '.join(result_store.remaining_hosts())
                error_message = 'Connect scan task failed with credential %s.'\
                    ' Error: %s Hosts: %s' %\
                    (credential.name, ansible_error, remaining_hosts_str)
                return error_message, ScanTask.FAILED

            remaining_hosts = result_store.remaining_hosts()

            logger.debug('Failed systems: %s', remaining_hosts)

        for host in remaining_hosts:
            # We haven't connected to these hosts with any
            # credentials, so they have failed.
            result_store.record_result(host, self.scan_task.source,
                                       None, SystemConnectionResult.FAILED)

        return None, ScanTask.COMPLETED


# pylint: disable=too-many-arguments
def connect(hosts, callback, credential, connection_port, forks=50):
    """Attempt to connect to hosts using the given credential.

    :param hosts: The collection of hosts to test connections
    :param callback: The Ansible callback to accept the results.
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param forks: number of forks to run with, default of 50
    :returns: list of connected hosts credential tuples and
            list of host that failed connection
    """
    inventory = construct_connect_inventory(hosts, credential, connection_port)
    inventory_file = write_inventory(inventory)
    extra_vars = {}

    playbook = {'name': 'discovery play',
                'hosts': 'all',
                'gather_facts': 'no',
                'tasks': [{'action': {'module': 'raw',
                                      'args': parse_kv('echo "Hello"')}}]}

    _handle_ssh_passphrase(credential)
    result = run_playbook(inventory_file, callback, playbook,
                          extra_vars, forks=forks)

    if (result != TaskQueueManager.RUN_OK and
            result != TaskQueueManager.RUN_UNREACHABLE_HOSTS and
            result != TaskQueueManager.RUN_FAILED_HOSTS):
        raise _construct_error(result)


def _handle_ssh_passphrase(credential):
    """Attempt to setup loggin via passphrase if necessary.

    :param credential: The credential used for connections
    """
    if (credential.get('ssh_keyfile') is not None and
            credential.get('ssh_passphrase') is not None):
        keyfile = credential.get('ssh_keyfile')
        passphrase = \
            decrypt_data_as_unicode(credential['ssh_passphrase'])
        cmd_string = 'ssh-add {}'.format(keyfile)

        try:
            child = pexpect.spawn(cmd_string, timeout=12)
            phrase = [pexpect.EOF, 'Enter passphrase for .*:']
            i = child.expect(phrase)
            child.sendline(passphrase)
            while i:
                i = child.expect(phrase)
        except pexpect.exceptions.TIMEOUT:
            pass


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
