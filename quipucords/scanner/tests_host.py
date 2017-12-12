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
from api.models import (Credential, Source, HostRange,
                        ScanTask, ScanJob, ConnectionResults, ConnectionResult,
                        SystemConnectionResult, InspectionResults)
from api.serializers import CredentialSerializer, SourceSerializer
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
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            ssh_port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scanjob = ScanJob(scan_type=ScanTask.HOST)
        self.scanjob.save()

        self.scanjob.sources = [self.source.id]
        self.scanjob.save()

        self.scanjob.failed_scans = 0
        self.scanjob.save()
        self.fact_endpoint = 'http://testserver' + reverse('facts-list')

        self.conn_results = ConnectionResults(scan_job=self.scanjob)
        self.conn_results.save()

        self.conn_result = ConnectionResult(source=self.source)
        self.conn_result.save()

        success_sys = SystemConnectionResult(
            name='1.2.3.4', credential=self.cred,
            status=SystemConnectionResult.SUCCESS)
        success_sys.save()
        failed_sys = SystemConnectionResult(
            name='1.1.1.2', status=SystemConnectionResult.FAILED)
        failed_sys.save()
        self.conn_result.systems.add(success_sys)
        self.conn_result.systems.add(failed_sys)
        self.conn_result.save()
        self.conn_results.results.add(self.conn_result)
        self.conn_results.save()

    def test_store_host_scan_success(self):
        """Test success storage."""
        scanner = HostScanner(self.scanjob, self.fact_endpoint)
        # pylint: disable=protected-access
        result = scanner._store_host_scan_success(1)
        self.assertTrue(isinstance(result, InspectionResults))

    def test_scan_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        connection_port = source['ssh_port']
        hc_serializer = CredentialSerializer(self.cred)
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
        serializer = SourceSerializer(self.source)
        source = serializer.data
        connection_port = source['ssh_port']
        hc_serializer = CredentialSerializer(self.cred)
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
                conn_results=self.conn_results)
            facts = scanner.run()
            mock_run.assert_called_with(ANY)
            self.assertEqual(facts, [])

    def test_populate_callback(self):
        """Test the population of the callback object for host scan."""
        inspect = InspectionResults(scan_job=self.scanjob)
        inspect.save()
        callback = ResultCallback(
            scanjob=self.scanjob, inspect_results=inspect)
        host = Mock()
        host.name = '1.2.3.4'
        result = Mock(_host=host, _results={'rc': 3})

        callback.v2_runner_on_unreachable(result)
