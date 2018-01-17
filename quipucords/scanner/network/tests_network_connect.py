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
"""Test the discovery scanner capabilities."""

from unittest.mock import patch, Mock, ANY
from django.test import TestCase
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from api.models import (Credential,
                        Source,
                        ConnectionResults,
                        HostRange,
                        ScanJob,
                        ScanOptions,
                        ScanTask)
from api.serializers import CredentialSerializer, SourceSerializer
from scanner.network.connect import (_construct_vars,
                                     _process_connect_callback,
                                     _construct_error,
                                     construct_connect_inventory, connect)
from scanner.network.utils import (ANSIBLE_FAILED_HOST_ERR_MSG,
                                   ANSIBLE_UNREACHABLE_HOST_ERR_MSG,
                                   ANSIBLE_PLAYBOOK_ERR_MSG)
from scanner.network import ConnectTaskRunner
from scanner.network.connect_callback import ConnectResultCallback


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success."""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure."""
    return 255


def mock_handle_ssh(cred):  # pylint: disable=unused-argument
    """Mock for handling ssh passphrase setting."""
    pass


class NetworkConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            sudo_password='sudo',
            ssh_keyfile='keyfile',
            become_method='sudo')
        self.cred.save()

        self.source = Source(
            name='source1',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scan_task = ScanTask(
            source=self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_task.systems_failed = 0
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.sources.add(self.source)
        self.scan_job.tasks.add(self.scan_task)
        scan_options = ScanOptions()
        scan_options.save()
        self.scan_job.options = scan_options
        self.scan_job.save()

        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()

    def test_construct_vars(self):
        """Test constructing ansible vars dictionary."""
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        vars_dict = _construct_vars(22, cred)
        expected = {'ansible_become_pass': 'sudo', 'ansible_port': 22,
                    'ansible_ssh_pass': 'password',
                    'ansible_ssh_private_key_file': 'keyfile',
                    'ansible_user': 'username',
                    'ansible_become_method': 'sudo'}
        self.assertEqual(vars_dict, expected)

    def test_populate_callback(self):
        """Test the population of the callback object."""
        callback = ConnectResultCallback()
        host = Mock(name='1.2.3.4')
        result = Mock(_host=host, _results={'rc': 0})
        callback.v2_runner_on_ok(result)
        self.assertTrue(len(callback.results) == 1)
        callback.v2_runner_on_failed(result)
        self.assertTrue(len(callback.results) == 2)
        callback.v2_runner_on_unreachable(result)
        self.assertTrue(len(callback.results) == 3)

    def test_process_connect_callback(self):
        """Test callback processing logic."""
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        callback = ConnectResultCallback()
        success_result = {'host': '1.2.3.4', 'result': {'rc': 0}}
        failed_result = {'host': '1.2.3.5', 'result': {'rc': 1}}
        failed_result_format = {'host': '1.2.3.6'}
        callback.results.append(success_result)
        callback.results.append(failed_result)
        callback.results.append(failed_result_format)
        success, failed = _process_connect_callback(callback, cred)
        del cred['password']
        self.assertEqual(success, [('1.2.3.4', cred)])
        self.assertEqual(failed, ['1.2.3.5', '1.2.3.6'])

    def test_connect_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_connect_inventory(hosts, cred,
                                                     connection_port)
        expected = {'all': {'hosts': {'1.2.3.4': None},
                            'vars': {'ansible_become_pass': 'sudo',
                                     'ansible_port': 22,
                                     'ansible_ssh_pass': 'password',
                                     'ansible_ssh_private_key_file': 'keyfile',
                                     'ansible_user': 'username',
                                     'ansible_become_method': 'sudo'}}}
        self.assertEqual(inventory_dict, expected)

    def test_construct_error(self):
        """Test the creation of different errors."""
        error = _construct_error(TaskQueueManager.RUN_FAILED_HOSTS)
        self.assertEqual(error.message, ANSIBLE_FAILED_HOST_ERR_MSG)
        error = _construct_error(TaskQueueManager.RUN_UNREACHABLE_HOSTS)
        self.assertEqual(error.message, ANSIBLE_UNREACHABLE_HOST_ERR_MSG)
        error = _construct_error(TaskQueueManager.RUN_FAILED_BREAK_PLAY)
        self.assertEqual(error.message, ANSIBLE_PLAYBOOK_ERR_MSG)

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_failed)
    @patch('scanner.network.connect._handle_ssh_passphrase',
           side_effect=mock_handle_ssh)
    def test_connect_failure(self, mock_run, mock_ssh_pass):
        """Test connect flow with mocked manager and failure."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        with self.assertRaises(AnsibleError):
            connect(hosts, cred, connection_port)
            mock_run.assert_called()
            mock_ssh_pass.assert_called()

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_success)
    def test_connect(self, mock_run):
        """Test connect flow with mocked manager."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        connected, failed = connect(hosts, cred, connection_port)
        self.assertEqual(connected, [])
        self.assertEqual(failed, [])
        mock_run.assert_called_with(ANY)

    @patch('scanner.network.connect.connect')
    def test_discovery(self, mock_connect):
        """Test running a discovery scan with mocked connection."""
        expected = ([('1.2.3.4', {'id': '1'})], [])
        mock_connect.return_value = expected
        scanner = ConnectTaskRunner(
            self.scan_job, self.scan_task, self.conn_results)
        conn_dict = scanner.run()
        mock_connect.assert_called_with(ANY, ANY, 22, forks=50)
        self.assertEqual(conn_dict, ScanTask.COMPLETED)

    def test_store_discovery_success(self):
        """Test running a discovery scan _store_connect_result."""
        scanner = ConnectTaskRunner(
            self.scan_job, self.scan_task, self.conn_results)
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        connected = [('1.2.3.4', cred)]
        failed = ['1.2.3.5']
        expected = {'1.2.3.4': {'name': 'cred1'},
                    '1.2.3.5': None}
        # pylint: disable=protected-access
        result = scanner._store_connect_result(connected, failed)
        self.assertEqual(len(result), len(expected))
        self.assertIn('1.2.3.5', result)
        self.assertIsNone(result['1.2.3.5'])
