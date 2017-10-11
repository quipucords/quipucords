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
"""Test the discovery scanner capabilities"""

from unittest.mock import patch, Mock
from django.test import TestCase
from api.hostcredential_model import HostCredential
from api.networkprofile_model import NetworkProfile, HostRange
from api.hostcredential_serializer import HostCredentialSerializer
from api.networkprofile_serializer import NetworkProfileSerializer
from api.scanjob_model import ScanJob
from scanner.utils import (_construct_vars, _process_connect_callback,
                           construct_inventory, connect)
from scanner.discovery import DiscoveryScanner
from scanner.callback import ResultCallback


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success"""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure"""
    return 255


class DiscoveryScannerTest(TestCase):
    """Tests against the DiscoveryScanner class and functions"""

    def setUp(self):
        self.cred = HostCredential(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.network_profile = NetworkProfile(
            name='profile1',
            ssh_port=22)
        self.network_profile.save()
        self.network_profile.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              network_profile_id=self.network_profile.id)
        self.host.save()

        self.network_profile.hosts.add(self.host)

        self.scanjob = ScanJob(profile_id=self.network_profile.id,
                               scan_type=ScanJob.DISCOVERY)
        self.scanjob.save()

    def test_construct_vars(self):
        """Test constructing ansible vars dictionary"""
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        vars_dict = _construct_vars(cred, 22)
        expected = {'ansible_port': 22, 'ansible_ssh_pass': 'password',
                    'ansible_user': 'username'}
        self.assertEqual(vars_dict, expected)

    def test_populate_callback(self):
        """Test the population of the callback object"""
        callback = ResultCallback()
        host = Mock(name='1.2.3.4')
        result = Mock(_host=host, _results={'rc': 0})
        callback.v2_runner_on_ok(result)
        self.assertTrue(len(callback.results) == 1)
        callback.v2_runner_on_failed(result)
        self.assertTrue(len(callback.results) == 2)
        callback.v2_runner_on_unreachable(result)
        self.assertTrue(len(callback.results) == 3)

    def test_process_connect_callback(self):
        """Test callback processing logic"""
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        callback = ResultCallback()
        success_result = {'host': '1.2.3.4', 'result': {'rc': 0}}
        failed_result = {'host': '1.2.3.5', 'result': {'rc': 1}}
        callback.results.append(success_result)
        callback.results.append(failed_result)
        success, failed = _process_connect_callback(callback, cred)
        del cred['password']
        self.assertEqual(success, [('1.2.3.4', cred)])
        self.assertEqual(failed, ['1.2.3.5'])

    def test_construct_inventory(self):
        """Test construct ansible inventory dictionary"""
        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        hosts = profile['hosts']
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_inventory(hosts, cred, connection_port)
        expected = {'all': {'hosts': {'1.2.3.4': None},
                            'vars': {'ansible_port': 22,
                                     'ansible_ssh_pass': 'password',
                                     'ansible_user': 'username'}}}
        self.assertEqual(inventory_dict, expected)

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_failed)
    def test_connect_failure(self, mock_run):
        """Test connect flow with mocked manager and failure"""

        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        hosts = profile['hosts']
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        connected, failed = connect(hosts, cred, connection_port)
        self.assertEqual(connected, [])
        self.assertEqual(failed, ['1.2.3.4'])
        mock_run.assert_called()

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_success)
    def test_connect(self, mock_run):
        """Test connect flow with mocked manager """
        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        hosts = profile['hosts']
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        connected, failed = connect(hosts, cred, connection_port)
        self.assertEqual(connected, [])
        self.assertEqual(failed, [])
        mock_run.assert_called()

    @patch('scanner.discovery.connect')
    def test_discovery(self, mock_connect):
        """Test running a discovery scan with mocked connection"""
        expected = ([('1.2.3.4', {'name': 'cred1'})], [])
        mock_connect.return_value = expected
        scanner = DiscoveryScanner(self.scanjob, self.network_profile)
        conn_dict = scanner.run()
        mock_connect.assert_called()
        self.assertEqual(conn_dict, {'1.2.3.4': {'name': 'cred1'}})
