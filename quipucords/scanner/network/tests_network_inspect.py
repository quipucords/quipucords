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
"""Test the inspect scanner capabilities."""

# pylint: disable=ungrouped-imports
import os.path
import unittest
from multiprocessing import Value
from unittest.mock import ANY, Mock, patch
from types import SimpleNamespace  # noqa: I100

from ansible.errors import AnsibleError

from api.models import (Credential,
                        ExtendedProductSearchOptions,
                        ScanJob,
                        ScanOptions,
                        ScanTask,
                        Source,
                        SourceOptions,
                        SystemConnectionResult)
from api.serializers import CredentialSerializer, SourceSerializer

from django.test import TestCase
from django.urls import reverse

import requests_mock

from scanner import scan_data_log
from scanner.network import InspectTaskRunner
from scanner.network.inspect import (_construct_scan_inventory)
from scanner.network.inspect_callback import (ANSIBLE_FACTS,
                                              InspectResultCallback,
                                              normalize_result)
from scanner.test_util import create_scan_job


def mock_run_success(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with success."""
    return 0


def mock_run_failed(play):  # pylint: disable=unused-argument
    """Mock for TaskQueueManager run method with failure."""
    return 255


def mock_scan_error(manager_interrupt, hosts):
    """Throws error."""
    # pylint: disable=unused-argument
    raise AnsibleError('an error')


class TestNormalizeResult(unittest.TestCase):
    """Tests for inspect_callback.normalize_result."""

    RESULT = {'rc': 0,
              'stdout': 'a',
              'stdout_lines': ['a']}

    def test_no_register(self):
        """A task with no register variable."""
        self.assertEqual(
            normalize_result(
                SimpleNamespace(_host=SimpleNamespace(name='hostname'),
                                _result=self.RESULT,
                                _task=SimpleNamespace(register=None))),
            [])

    def test_register_internal(self):
        """A task that registers an internal variable."""
        self.assertEqual(
            normalize_result(
                SimpleNamespace(
                    _host=SimpleNamespace(name='hostname'),
                    _result=self.RESULT,
                    _task=SimpleNamespace(register='internal_name'))),
            [('internal_name',
              {'rc': 0, 'stdout': 'a', 'stdout_lines': ['a']})])

    def test_register_not_internal(self):
        """A task that registers a non-internal variable."""
        self.assertEqual(
            normalize_result(
                SimpleNamespace(
                    _host=SimpleNamespace(name='hostname'),
                    _result=self.RESULT,
                    _task=SimpleNamespace(register='name'))),
            [('name', self.RESULT)])

    def test_register_ansible_fact(self):
        """A set_facts task that registers one fact."""
        self.assertEqual(
            normalize_result(
                SimpleNamespace(
                    _host=SimpleNamespace(name='hostname'),
                    _result={ANSIBLE_FACTS:
                             {'fact': 'fact_result'}},
                    _task=SimpleNamespace(register='name'))),
            [('fact', 'fact_result')])

    def test_register_ansible_facts(self):
        """A set_facts task that registers multiple facts."""
        self.assertEqual(
            # Wrap normalize_result in set() to make comparison
            # independent of order.
            set(normalize_result(
                SimpleNamespace(
                    _host=SimpleNamespace(name='hostname'),
                    _result={ANSIBLE_FACTS:
                             {'fact1': 'result1',
                              'fact2': 'result2',
                              'fact3': 'result3'}},
                    _task=SimpleNamespace(register='name')))),
            {('fact1', 'result1'),
             ('fact2', 'result2'),
             ('fact3', 'result3')})

    def test_internal_ansible_fact(self):
        """A set_facts task that registers an internal fact."""
        self.assertEqual(
            normalize_result(
                SimpleNamespace(
                    _host=SimpleNamespace(name='hostname'),
                    _result={ANSIBLE_FACTS:
                             {'internal_fact': 'fact_result'}},
                    _task=SimpleNamespace(register='name'))),
            [('internal_fact', 'fact_result')])


class NetworkInspectScannerTest(TestCase):
    """Tests network inspect scan task class."""

    # pylint: disable=too-many-instance-attributes, protected-access
    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            ssh_keyfile=None,
            become_method=None,
            become_user=None,
            become_password=None)
        self.cred.save()

        hc_serializer = CredentialSerializer(self.cred)
        self.cred_data = hc_serializer.data

        # setup source for scan
        self.source = Source(
            name='source1',
            port=22,
            hosts='["1.2.3.4"]')
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host_list = [('1.2.3.4', self.cred_data)]

        self.scan_job, self.scan_task = create_scan_job(
            self.source,
            ScanTask.SCAN_TYPE_INSPECT)

        self.connect_scan_task = self.scan_task.prerequisites.first()
        self.connect_scan_task.update_stats(
            'TEST NETWORK CONNECT.', sys_failed=0)

        conn_result = self.connect_scan_task.connection_result
        success_sys = SystemConnectionResult(
            name='1.2.3.4', credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result)
        success_sys.save()
        failed_sys = SystemConnectionResult(
            name='1.1.1.2', status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result)
        failed_sys.save()
        conn_result.save()

        self.connect_scan_task.update_stats(
            'TEST_VC.', sys_count=2, sys_failed=1, sys_scanned=1)
        self.connect_scan_task.complete()

        self.scan_task.update_stats(
            'TEST NETWORK INSPECT.', sys_failed=0)

        self.fact_endpoint = 'http://testserver' + reverse('reports-list')

        self.scan_job.save()

        scan_data_log.disable_log_for_test()

    def test_scan_inventory(self):
        """Test construct ansible inventory dictionary."""
        serializer = SourceSerializer(self.source)
        source = serializer.data
        connection_port = source['port']
        inventory_dict = _construct_scan_inventory(self.host_list,
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
        connection_port = source['port']
        hc_serializer = CredentialSerializer(self.cred)
        cred = hc_serializer.data
        inventory_dict = _construct_scan_inventory(
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

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_failed)
    def test_inspect_scan_failure(self, mock_run):
        """Test scan flow with mocked manager and failure."""
        scanner = InspectTaskRunner(
            self.scan_job, self.scan_task)

        # Init for unit test as run is not called
        scanner.connect_scan_task = self.connect_scan_task
        with self.assertRaises(AnsibleError):
            scanner._inspect_scan(Value('i', ScanJob.JOB_RUN), self.host_list)
            mock_run.assert_called()

    @patch('scanner.network.inspect.InspectTaskRunner._inspect_scan',
           side_effect=mock_scan_error)
    def test_inspect_scan_error(self, mock_scan):
        """Test scan flow with mocked manager and failure."""
        scanner = InspectTaskRunner(
            self.scan_job, self.scan_task)
        scan_task_status = scanner.run(Value('i', ScanJob.JOB_RUN))
        mock_scan.assert_called_with(ANY, self.host_list)
        self.assertEqual(scan_task_status[1], ScanTask.FAILED)

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_success)
    def test_inspect_scan_fail_no_facts(self, mock_run):
        """Test running a inspect scan with mocked connection."""
        expected = ([('1.2.3.4', {'name': 'cred1'})], [])
        mock_run.return_value = expected
        with requests_mock.Mocker() as mocker:
            mocker.post(self.fact_endpoint, status_code=201, json={'id': 1})
            scanner = InspectTaskRunner(
                self.scan_job, self.scan_task)
            scan_task_status = scanner.run(Value('i', ScanJob.JOB_RUN))
            mock_run.assert_called_with(ANY)
            self.assertEqual(scan_task_status[1], ScanTask.FAILED)

    def test_populate_callback(self):
        """Test the population of the callback object for inspect scan."""
        callback = InspectResultCallback(
            scan_task=self.scan_task)
        host = Mock()
        host.name = '1.2.3.4'
        task = Mock(args={'_raw_params': 'command line'})
        result = Mock(_host=host, _result={'rc': 3}, _task=task)

        callback.v2_runner_on_unreachable(result)

    def test_ssh_crash(self):
        """Simulate an ssh crash."""
        scanner = InspectTaskRunner(
            self.scan_job, self.scan_task)
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '../../../test_util/crash.py'))
        _, result = scanner._inspect_scan(
            Value('i', ScanJob.JOB_RUN),
            self.host_list,
            base_ssh_executable=path)
        self.assertEqual(result, ScanTask.COMPLETED)

    def test_ssh_hang(self):
        """Simulate an ssh hang."""
        scanner = InspectTaskRunner(
            self.scan_job, self.scan_task)
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '../../../test_util/hang.py'))
        scanner._inspect_scan(
            Value('i', ScanJob.JOB_RUN),
            self.host_list,
            roles=['redhat_release'],
            base_ssh_executable=path,
            ssh_timeout='0.1s')

    @patch('scanner.network.utils.TaskQueueManager.run',
           side_effect=mock_run_success)
    def test_scan_with_options(self, mock_run):
        """Setup second scan with scan and source options."""
        # setup source with paramiko option for scan
        source_options = SourceOptions()
        source_options.save()
        self.source = Source(
            name='source2',
            port=22,
            options=source_options,
            hosts='["1.2.3.4"]')
        self.source.save()
        self.source.credentials.add(self.cred)

        # setup scan with options
        extended = ExtendedProductSearchOptions()
        extended.save()
        scan_options = ScanOptions(
            enabled_extended_product_search=extended)
        scan_options.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source,
            ScanTask.SCAN_TYPE_INSPECT,
            'scan2',
            scan_options=scan_options)

        # run scan
        scanner = InspectTaskRunner(
            self.scan_job, self.scan_task)

        scanner.connect_scan_task = self.connect_scan_task
        scanner._inspect_scan(Value('i', ScanJob.JOB_RUN), self.host_list)
        mock_run.assert_called_with(ANY)
