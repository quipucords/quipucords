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
"""Test the vcenter connect capabilities."""

from datetime import datetime
from unittest.mock import Mock, patch, ANY
from socket import gaierror
from django.test import TestCase
from pyVmomi import vim  # pylint: disable=no-name-in-module
from api.models import (Credential, Source, ScanTask,
                        ScanJob, JobConnectionResult, TaskConnectionResult)
from scanner.vcenter.connect import (ConnectTaskRunner, get_vm_names,
                                     get_vm_container)


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


def unreachable_host():
    """Mock with gaierror."""
    raise gaierror('Unreachable')


class ConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    runner = None

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=22,
            hosts='["1.2.3.4"]')

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=2,
                                  start_time=datetime.utcnow())
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = JobConnectionResult()
        self.conn_results.save()
        self.scan_job.connection_results = self.conn_results
        self.scan_job.save()

        self.runner = ConnectTaskRunner(scan_job=self.scan_job,
                                        scan_task=self.scan_task)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_store_connect_data(self):
        """Test the connection data method."""
        vm_names = ['vm1', 'vm2']
        # pylint: disable=protected-access
        self.runner._store_connect_data(vm_names, self.cred)
        self.assertEqual(len(self.conn_results.results.all()), 1)
        result = self.conn_results.results.all().first()
        self.assertEqual(result.scan_task, self.scan_task)
        self.assertEqual(result.source, self.source)

    def test_get_vm_names(self):
        """Test the get vm names method."""
        children = []
        for ident in range(1, 3):
            name = 'vm' + str(ident)
            config = Mock()
            config.name = name
            summary = Mock()
            summary.config = config
            child = Mock()
            child.summary = summary
            children.append(child)
        vm_container_view = Mock(view=children)
        vm_names = get_vm_names(vm_container_view)
        self.assertTrue(isinstance(vm_names, list))
        self.assertEqual(vm_names, ['vm1', 'vm2'])

    def test_get_vm_container(self):
        """Get the VM container."""
        vcenter = Mock()
        content = Mock()
        content.rootFolder = Mock()
        view_manager = Mock()
        container_view = Mock()
        view_manager.CreateContainerView = Mock(return_value=container_view)
        content.viewManager = view_manager
        vcenter.RetrieveContent = Mock(return_value=content)
        c_view = get_vm_container(vcenter)
        self.assertEqual(c_view, container_view)

    def test_connect(self):
        """Test the VCenter connect method."""
        with patch('scanner.vcenter.connect.vcenter_connect',
                   return_value=Mock()) as mock_vcenter_connect:
            with patch('scanner.vcenter.connect.get_vm_container',
                       return_value=Mock()) as mock_get_vm_container:
                with patch('scanner.vcenter.connect.get_vm_names',
                           return_value=['vm1', 'vm2']) as mock_names:
                    vm_names = self.runner.connect()
                    self.assertEqual(vm_names, set(['vm1', 'vm2']))
                    mock_vcenter_connect.assert_called_once_with(ANY)
                    mock_get_vm_container.assert_called_once_with(ANY)
                    mock_names.assert_called_once_with(ANY)

    def test_get_result_none(self):
        """Test get result method when no results exist."""
        results = self.runner.get_result()
        self.assertEqual(results, None)

    def test_get_result(self):
        """Test get result method when results exist."""
        conn_result = TaskConnectionResult(source=self.source,
                                           scan_task=self.scan_task)
        conn_result.save()
        self.conn_results.results.add(conn_result)
        self.conn_results.save()
        results = self.runner.get_result()
        self.assertEqual(results, conn_result)

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(ConnectTaskRunner, 'connect',
                          side_effect=invalid_login) as mock_connect:
            status = self.runner.run()
            self.assertEqual(ScanTask.FAILED, status[1])
            mock_connect.assert_called_once_with()

    def test_unreachable_run(self):
        """Test the run method with unreachable."""
        with patch.object(ConnectTaskRunner, 'connect',
                          side_effect=unreachable_host) as mock_connect:
            status = self.runner.run()
            self.assertEqual(ScanTask.FAILED, status[1])
            mock_connect.assert_called_once_with()

    def test_run(self):
        """Test the run method."""
        with patch.object(ConnectTaskRunner, 'connect',
                          return_value=['vm1', 'vm2']) as mock_connect:
            status = self.runner.run()
            self.assertEqual(ScanTask.COMPLETED, status[1])
            mock_connect.assert_called_once_with()
