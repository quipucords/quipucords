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
"""Test the discovery scanner capabilities."""

import unittest
from unittest.mock import ANY, Mock, patch

from ansible.errors import AnsibleError

from api.connresults.model import SystemConnectionResult
from api.models import (Credential,
                        ScanTask,
                        Source)
from api.serializers import CredentialSerializer, SourceSerializer

from django.test import TestCase


from scanner.network import ConnectTaskRunner
from scanner.network.connect import (ConnectResultStore,
                                     connect,
                                     construct_connect_inventory)
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import _construct_vars
from scanner.test_util import create_scan_job


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success."""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure."""
    return 255


def mock_handle_ssh(cred):  # pylint: disable=unused-argument
    """Mock for handling ssh passphrase setting."""
    pass


class MockResultStore(object):
    """A mock ConnectResultStore."""

    def __init__(self, hosts):
        """Minimal internal variables, just to fake the state."""
        self._remaining_hosts = set(hosts)
        self.succeeded = []
        self.failed = []

    def record_result(self, name, source, credential, status):
        """Keep a list of succeeses and failures."""
        if status == SystemConnectionResult.SUCCESS:
            self.succeeded.append((name, source, credential, status))
        elif status == SystemConnectionResult.FAILED:
            self.failed.append((name, source, credential, status))
        else:
            raise ValueError()

        self._remaining_hosts.remove(name)

    def remaining_hosts(self):
        """Need this method because the task runner uses it."""
        return list(self._remaining_hosts)


def make_result(hostname, rc):  # pylint: disable=invalid-name
    """Mock the result structure that Ansible pass the callback."""
    if rc is not None:
        result = {'rc': rc}
    else:
        result = {}

    host = Mock()
    host.name = hostname

    return Mock(
        _host=host,
        _result=result)


class TestConnectResultCallback(unittest.TestCase):
    """Test ConnectResultCallback."""

    def test_callback(self):
        """Test the callback."""
        result_store = MockResultStore(['host1', 'host2', 'host3'])
        credential = Mock(name='credential')
        source = Mock(name='source')
        callback = ConnectResultCallback(result_store, credential,
                                         source)
        callback.v2_runner_on_ok(make_result('host1', 0))
        callback.v2_runner_on_ok(make_result('host2', 1))
        callback.v2_runner_on_ok(make_result('host3', None))

        self.assertEqual(result_store.succeeded,
                         [('host1', source, credential, 'success')])
        self.assertEqual(result_store.failed, [])


class NetworkConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            ssh_keyfile='keyfile',
            become_method='sudo',
            become_user='root',
            become_password='become')
        self.cred.save()

        # Source with excluded hosts
        self.source = Source(
            name='source1',
            hosts='["1.2.3.4", "1.2.3.5"]',
            exclude_hosts='["1.2.3.5", "1.2.3.6"]',
            source_type='network',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)
        self.source.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT)

        self.scan_task.update_stats('TEST NETWORK CONNECT.', sys_failed=0)

        # Source without excluded hosts
        self.source2 = Source(
            name='source2',
            hosts='["1.2.3.4"]',
            source_type='network',
            port=22)
        self.source2.save()
        self.source2.credentials.add(self.cred)
        self.source2.save()

        self.scan_job2, self.scan_task2 = create_scan_job(
            self.source, 'source2', ScanTask.SCAN_TYPE_CONNECT)

        self.scan_task2.update_stats('TEST NETWORK CONNECT.', sys_failed=0)

    def test_construct_vars(self):
        """Test constructing ansible vars dictionary."""
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        vars_dict = _construct_vars(22, cred)
        expected = {'ansible_become_pass': 'become',
                    'ansible_port': 22,
                    'ansible_ssh_pass': 'password',
                    'ansible_ssh_private_key_file': 'keyfile',
                    'ansible_user': 'username',
                    'ansible_become_method': 'sudo',
                    'ansible_become_user': 'root'}
        self.assertEqual(vars_dict, expected)

    def test_get_exclude_host(self):
        """Test get_exclude_hosts() method."""
        assert self.source.get_exclude_hosts() != []
        assert self.source2.get_exclude_hosts() == []

    # Tests for source1 (has hosts and excluded host)
    def test_result_store(self):
        """Test ConnectResultStore."""
        result_store = ConnectResultStore(self.scan_task)

        self.assertEqual(result_store.remaining_hosts(), ['1.2.3.4'])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 0)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

        result_store.record_result('1.2.3.4', self.source, self.cred,
                                   SystemConnectionResult.SUCCESS)

        self.assertEqual(result_store.remaining_hosts(), [])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 1)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

    def test_connect_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        exclude_hosts = source['exclude_hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_connect_inventory(hosts, cred,
                                                     connection_port,
                                                     exclude_hosts)
        expected = {'all': {'hosts': {'1.2.3.4': None},
                            'vars': {'ansible_become_pass': 'become',
                                     'ansible_port': 22,
                                     'ansible_ssh_pass': 'password',
                                     'ansible_ssh_private_key_file': 'keyfile',
                                     'ansible_user': 'username',
                                     'ansible_become_method': 'sudo',
                                     'ansible_become_user': 'root'}}}
        self.assertEqual(inventory_dict, expected)

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_failed)
    @patch('scanner.network.connect._handle_ssh_passphrase',
           side_effect=mock_handle_ssh)
    def test_connect_failure(self, mock_run, mock_ssh_pass):
        """Test connect flow with mocked manager and failure."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        exclude_hosts = source['exclude_hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        with self.assertRaises(AnsibleError):
            connect(hosts, Mock(), cred, connection_port, exclude_hosts)
            mock_run.assert_called()
            mock_ssh_pass.assert_called()

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_success)
    def test_connect(self, mock_run):
        """Test connect flow with mocked manager."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        hosts = source['hosts']
        exclude_hosts = source['exclude_hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        connect(hosts, Mock(), cred, connection_port, exclude_hosts)
        mock_run.assert_called_with(ANY)

    @patch('scanner.network.connect.connect')
    def test_connect_runner(self, mock_connect):
        """Test running a connect scan with mocked connection."""
        scanner = ConnectTaskRunner(self.scan_job, self.scan_task)
        result_store = MockResultStore(['1.2.3.4'])
        conn_dict = scanner.run_with_result_store(result_store)
        mock_connect.assert_called_with(ANY, ANY, ANY, 22, forks=50)
        self.assertEqual(conn_dict[1], ScanTask.COMPLETED)

    # Similar tests as above modified for source2 (Does not have exclude hosts)
    def test_result_store_src2(self):
        """Test ConnectResultStore."""
        result_store = ConnectResultStore(self.scan_task2)

        self.assertEqual(result_store.remaining_hosts(), ['1.2.3.4'])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 0)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

        result_store.record_result('1.2.3.4', self.source2, self.cred,
                                   SystemConnectionResult.SUCCESS)

        self.assertEqual(result_store.remaining_hosts(), [])
        self.assertEqual(result_store.scan_task.systems_count, 1)
        self.assertEqual(result_store.scan_task.systems_scanned, 1)
        self.assertEqual(result_store.scan_task.systems_failed, 0)

    def test_connect_inventory_src2(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_connect_inventory(hosts, cred,
                                                     connection_port)
        expected = {'all': {'hosts': {'1.2.3.4': None},
                            'vars': {'ansible_become_pass': 'become',
                                     'ansible_port': 22,
                                     'ansible_ssh_pass': 'password',
                                     'ansible_ssh_private_key_file': 'keyfile',
                                     'ansible_user': 'username',
                                     'ansible_become_method': 'sudo',
                                     'ansible_become_user': 'root'}}}
        self.assertEqual(inventory_dict, expected)

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_failed)
    @patch('scanner.network.connect._handle_ssh_passphrase',
           side_effect=mock_handle_ssh)
    def test_connect_failure_src2(self, mock_run, mock_ssh_pass):
        """Test connect flow with mocked manager and failure."""
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        with self.assertRaises(AnsibleError):
            connect(hosts, Mock(), cred, connection_port)
            mock_run.assert_called()
            mock_ssh_pass.assert_called()

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_success)
    def test_connect_src2(self, mock_run):
        """Test connect flow with mocked manager."""
        serializer = SourceSerializer(self.source2)
        source = serializer.data
        hosts = source['hosts']
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        connect(hosts, Mock(), cred, connection_port)
        mock_run.assert_called_with(ANY)

    @patch('scanner.network.connect.connect')
    def test_connect_runner_src2(self, mock_connect):
        """Test running a connect scan with mocked connection."""
        scanner = ConnectTaskRunner(self.scan_job2, self.scan_task2)
        result_store = MockResultStore(['1.2.3.4'])
        conn_dict = scanner.run_with_result_store(result_store)
        mock_connect.assert_called_with(ANY, ANY, ANY, 22, forks=50)
        self.assertEqual(conn_dict[1], ScanTask.COMPLETED)
