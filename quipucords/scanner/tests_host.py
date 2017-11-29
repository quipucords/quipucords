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
"""Test the host scanner capabilities."""

from unittest.mock import patch, Mock, ANY
from django.test import TestCase
from django.core.urlresolvers import reverse
import requests_mock
from ansible.errors import AnsibleError
from api.models import (HostCredential, NetworkProfile, HostRange,
                        ScanJob, ScanJobResults, Results, ResultKeyValue)
from api.serializers import HostCredentialSerializer, NetworkProfileSerializer
from scanner.utils import (construct_scan_inventory)
from scanner.host import HostScanner
from scanner.callback import ResultCallback


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success."""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure."""
    return 255


def mock_scan_error():
    """Throws error."""
    raise AnsibleError('an error')


class HostScannerTest(TestCase):
    """Tests against the HostScanner class and functions."""

    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        """Create test case setup."""
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
                               scan_type=ScanJob.HOST)
        self.scanjob.failed_scans = 0
        self.scanjob.save()
        self.fact_endpoint = 'http://testserver' + reverse('facts-list')

        self.scan_results = ScanJobResults(scan_job=self.scanjob,
                                           fact_collection_id=1)
        self.scan_results.save()

        self.success_row = Results(row='success')
        self.success_row.save()

        success_cols = ResultKeyValue(key='1.2.3.4', value='cred1')
        success_cols.save()
        self.success_row.columns.add(success_cols)
        self.success_row.save()
        self.scan_results.results.add(self.success_row)

        self.failed_row = Results(row='failed')
        self.failed_row.save()

        failed_cols = ResultKeyValue(key='1.1.1.2', value='None')
        failed_cols.save()
        self.failed_row.columns.add(failed_cols)
        self.failed_row.save()
        self.scan_results.results.add(self.failed_row)

        self.scan_results.save()

    def test_store_host_scan_success(self):
        """Test success storage."""
        scanner = HostScanner(self.scanjob, self.fact_endpoint)
        # pylint: disable=protected-access
        result = scanner._store_host_scan_success(1)
        self.assertTrue(isinstance(result, ScanJobResults))
        self.assertEqual(result.fact_collection_id, 1)

    def test_scan_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_scan_inventory([('1.2.3.4', cred)],
                                                  connection_port,
                                                  50)
        expected = {
            'all': {
                'children': {
                    'group_0': {
                        'hosts': {
                            '1.2.3.4': {
                                'ansible_user': 'username',
                                'ansible_ssh_pass': 'password',
                                'ansible_host': '1.2.3.4'}
                        }
                    }
                },
                'vars': {
                    'ansible_port': 22}
            }
        }

        self.assertEqual(inventory_dict[1], expected)

    def test_scan_inventory_grouping(self):
        """Test construct ansible inventory dictionary."""
        serializer = NetworkProfileSerializer(self.network_profile)
        profile = serializer.data
        connection_port = profile['ssh_port']
        hc_serializer = HostCredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = construct_scan_inventory(
            [
                ('1.2.3.1', cred),
                ('1.2.3.2', cred),
                ('1.2.3.3', cred),
                ('1.2.3.4', cred)
            ],
            connection_port,
            1)
        expected = {
            'all': {
                'children': {
                    'group_0': {
                        'hosts': {
                            '1.2.3.1': {
                                'ansible_user': 'username',
                                'ansible_ssh_pass': 'password',
                                'ansible_host': '1.2.3.1'}
                        }
                    },
                    'group_1': {
                        'hosts': {
                            '1.2.3.2': {
                                'ansible_user': 'username',
                                'ansible_ssh_pass': 'password',
                                'ansible_host': '1.2.3.2'}
                        }
                    },
                    'group_2': {
                        'hosts': {
                            '1.2.3.3': {
                                'ansible_user': 'username',
                                'ansible_ssh_pass': 'password',
                                'ansible_host': '1.2.3.3'}
                        }
                    },
                    'group_3': {
                        'hosts': {
                            '1.2.3.4': {
                                'ansible_user': 'username',
                                'ansible_ssh_pass': 'password',
                                'ansible_host': '1.2.3.4'}
                        }
                    }
                },
                'vars': {
                    'ansible_port': 22}
            }
        }

        self.assertEqual(inventory_dict[1], expected)

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_failed)
    def test_host_scan_failure(self, mock_run):
        """Test scan flow with mocked manager and failure."""
        scanner = HostScanner(self.scanjob, self.fact_endpoint)
        with self.assertRaises(AnsibleError):
            scanner.host_scan()
            mock_run.assert_called()

    @patch('scanner.host.HostScanner.host_scan', side_effect=mock_scan_error)
    def test_host_scan_error(self, mock_scan):
        """Test scan flow with mocked manager and failure."""
        scanner = HostScanner(self.scanjob, self.fact_endpoint)
        facts = scanner.run()
        mock_scan.assert_called_with()
        self.assertEqual(facts, [])

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_success)
    def test_host_scan(self, mock_run):
        """Test running a host scan with mocked connection."""
        expected = ([('1.2.3.4', {'name': 'cred1'})], [])
        mock_run.return_value = expected
        with requests_mock.Mocker() as mocker:
            mocker.post(self.fact_endpoint, status_code=201, json={'id': 1})
            scanner = HostScanner(self.scanjob, self.fact_endpoint)
            facts = scanner.run()
            mock_run.assert_called_with(ANY)
            self.assertEqual(facts, [])

    @patch('scanner.utils.TaskQueueManager.run', side_effect=mock_run_success)
    def test_host_scan_restart(self, mock_run):
        """Test restarting a host scan with mocked connection."""
        expected = ([('1.2.3.4', {'name': 'cred1'})], [])
        mock_run.return_value = expected
        with requests_mock.Mocker() as mocker:
            mocker.post(self.fact_endpoint, status_code=201, json={'id': 1})
            scanner = HostScanner(
                self.scanjob,
                self.fact_endpoint,
                scan_results=self.scan_results)
            facts = scanner.run()
            mock_run.assert_called_with(ANY)
            self.assertEqual(facts, [])

    def test_populate_callback(self):
        """Test the population of the callback object for host scan."""
        callback = ResultCallback(
            scanjob=self.scanjob, scan_results=self.scan_results)
        host = Mock()
        host.name = '1.2.3.4'
        result = Mock(_host=host, _results={'rc': 3})

        success_result = self.scan_results.results.all()[0]
        failed_result = self.scan_results.results.all()[1]

        self.assertEqual(_is_host_in_result(
            host.name, success_result), True)
        self.assertEqual(_is_host_in_result(
            host.name, failed_result), False)

        callback.v2_runner_on_unreachable(result)

        self.assertEqual(_is_host_in_result(
            host.name, success_result), False)
        self.assertEqual(_is_host_in_result(
            host.name, failed_result), True)


def _is_host_in_result(host, result):
    found = False
    for column in result.columns.all():
        if column.key == host:
            found = True
            break

    return found
