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
from multiprocessing import Value
from socket import gaierror
from unittest.mock import ANY, Mock, patch

from django.test import TestCase
from pyVmomi import vim  # pylint: disable=no-name-in-module

from api.models import Credential, ScanJob, ScanTask, Source
from scanner.test_util import create_scan_job
from scanner.vcenter.connect import ConnectTaskRunner, get_vm_names


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


def unreachable_host():
    """Mock with gaierror."""
    raise gaierror("Unreachable")


class ConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    runner = None

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(name="source1", port=22, hosts='["1.2.3.4"]')

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create runner
        self.runner = ConnectTaskRunner(
            scan_job=self.scan_job, scan_task=self.scan_task
        )

    def tearDown(self):
        """Cleanup test case setup."""

    def test_store_connect_data(self):
        """Test the connection data method."""
        vm_names = ["vm1", "vm2"]
        # pylint: disable=protected-access
        self.runner._store_connect_data(vm_names, self.cred, self.source)
        self.assertEqual(len(self.scan_job.connection_results.task_results.all()), 1)

    def test_get_vm_names(self):
        """Test the get vm names method."""
        objects = [
            vim.ObjectContent(
                obj=vim.VirtualMachine("vm-1"),
                propSet=[vim.DynamicProperty(name="name", val="vm1")],
            ),
            vim.ObjectContent(
                obj=vim.VirtualMachine("vm-2"),
                propSet=[vim.DynamicProperty(name="name", val="vm2")],
            ),
        ]

        content = Mock()
        content.rootFolder = vim.Folder("group-d1")
        content.propertyCollector.RetrievePropertiesEx(ANY).token = None
        content.propertyCollector.RetrievePropertiesEx(ANY).objects = objects

        vm_names = get_vm_names(content)
        self.assertTrue(isinstance(vm_names, list))
        self.assertEqual(vm_names, ["vm1", "vm2"])

    def test_connect(self):
        """Test the VCenter connect method."""
        with patch(
            "scanner.vcenter.connect.vcenter_connect", return_value=Mock()
        ) as mock_vcenter_connect:
            with patch(
                "scanner.vcenter.connect.get_vm_names",
                return_value=["vm1", "vm2", "vm2"],
            ) as mock_names:
                vm_names = self.runner.connect()
                self.assertEqual(vm_names, ["vm1", "vm2", "vm2"])
                mock_vcenter_connect.assert_called_once_with(ANY)
                mock_names.assert_called_once_with(ANY)

    def test_get_result_none(self):
        """Test get result method when no results exist."""
        results = self.scan_task.get_result().systems.first()
        self.assertEqual(results, None)

    def test_get_result(self):
        """Test get result method when results exist."""
        conn_result = self.scan_task.connection_result
        results = self.scan_task.get_result()
        self.assertEqual(results, conn_result)

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(
            ConnectTaskRunner, "connect", side_effect=invalid_login
        ) as mock_connect:
            status = self.runner.run(Value("i", ScanJob.JOB_RUN))
            self.assertEqual(ScanTask.FAILED, status[1])
            mock_connect.assert_called_once_with()

    def test_unreachable_run(self):
        """Test the run method with unreachable."""
        with patch.object(
            ConnectTaskRunner, "connect", side_effect=unreachable_host
        ) as mock_connect:
            status = self.runner.run(Value("i", ScanJob.JOB_RUN))
            self.assertEqual(ScanTask.FAILED, status[1])
            mock_connect.assert_called_once_with()

    def test_run(self):
        """Test the run method."""
        with patch.object(
            ConnectTaskRunner, "connect", return_value=["vm1", "vm2"]
        ) as mock_connect:
            status = self.runner.run(Value("i", ScanJob.JOB_RUN))
            self.assertEqual(ScanTask.COMPLETED, status[1])
            mock_connect.assert_called_once_with()

    def test_cancel(self):
        """Test the run method with cancel."""
        status = self.runner.run(Value("i", ScanJob.JOB_TERMINATE_CANCEL))
        self.assertEqual(ScanTask.CANCELED, status[1])

    def test_pause(self):
        """Test the run method with pause."""
        status = self.runner.run(Value("i", ScanJob.JOB_TERMINATE_PAUSE))
        self.assertEqual(ScanTask.PAUSED, status[1])
