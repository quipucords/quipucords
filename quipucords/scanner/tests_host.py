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
"""Test the host scanner capabilities"""

from unittest.mock import patch
from django.test import TestCase
from django.core.urlresolvers import reverse
import requests_mock
from ansible.errors import AnsibleError
from api.hostcredential_model import HostCredential
from api.networkprofile_model import NetworkProfile, HostRange
from api.hostcredential_serializer import HostCredentialSerializer
from api.networkprofile_serializer import NetworkProfileSerializer
from api.scanjob_model import ScanJob
from api.scanresults_model import ScanJobResults
from scanner.utils import (construct_scan_inventory)
from scanner.host import HostScanner


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success"""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure"""
    return 255


def mock_scan_error():
    """Throws error"""
    raise AnsibleError("an error")


class HostScannerTest(TestCase):
    """Tests against the HostScanner class and functions"""

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
        self.fact_endpoint = 'http://testserver' + reverse('facts-list')

    def test_store_host_scan_success(self):
        """Test success storage"""
        scanner = HostScanner(self.scanjob, self.network_profile,
                              self.fact_endpoint)
        facts = [{'key1': 'value1', 'key2': 'value2'}]
        # pylint: disable=protected-access
        result = scanner._store_host_scan_success(facts, 1)
        self.assertTrue(isinstance(result, ScanJobResults))
        self.assertEqual(len(result.results.all()), 1)

    def test_scan_inventory(self):
        """Test construct ansible inventory dictionary"""
        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_scan_inventory([('1.2.3.4', cred)],
                                                  connection_port)
        expected = {'all': {'hosts':
                            {'1.2.3.4': {'ansible_host': '1.2.3.4',
                                         'ansible_ssh_pass': 'password',
                                         'ansible_user': 'username'}},
                            'vars': {'ansible_port': 22}}}
        self.assertEqual(inventory_dict, expected)

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_failed)
    def test_host_scan_failure(self, mock_run):
        """Test scan flow with mocked manager and failure"""
        scanner = HostScanner(self.scanjob, self.network_profile,
                              self.fact_endpoint)
        with self.assertRaises(AnsibleError):
            scanner.host_scan()
            mock_run.assert_called()

    @patch('scanner.host.HostScanner.host_scan', side_effect=mock_scan_error)
    def test_host_scan_error(self, mock_scan):
        """Test scan flow with mocked manager and failure"""
        scanner = HostScanner(self.scanjob, self.network_profile,
                              self.fact_endpoint)
        facts = scanner.run()
        mock_scan.assert_called()
        self.assertEqual(facts, [])

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_success)
    def test_host_scan(self, mock_run):
        """Test running a host scan with mocked connection"""
        expected = ([('1.2.3.4', {'name': 'cred1'})], [])
        mock_run.return_value = expected
        with requests_mock.Mocker() as mocker:
            mocker.post(self.fact_endpoint, status_code=201, json={'id': 1})
            scanner = HostScanner(self.scanjob, self.network_profile,
                                  self.fact_endpoint)
            facts = scanner.run()
            mock_run.assert_called()
            self.assertEqual(facts, [])
