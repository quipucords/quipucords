"""Test the vcenter connect capabilities."""

from socket import gaierror
from unittest.mock import ANY, Mock, patch

import pytest
from pyVmomi import vim

from api.models import Credential, ScanTask, Source
from scanner.vcenter.connect import ConnectTaskRunner, get_vm_names
from tests.scanner.test_util import create_scan_job


def invalid_login():
    """Mock with invalid login exception."""
    raise vim.fault.InvalidLogin()


def unreachable_host():
    """Mock with gaierror."""
    raise gaierror("Unreachable")


@pytest.mark.django_db
class TestVCenterConnectTaskRunnerTest:
    """Tests against the ConnectTaskRunner class and functions."""

    runner = None

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(name="source1", port=22, hosts=["1.2.3.4"])

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create runner
        self.runner = ConnectTaskRunner(
            scan_job=self.scan_job, scan_task=self.scan_task
        )

    def test_store_connect_data(self):
        """Test the connection data method."""
        vm_names = ["vm1", "vm2"]

        self.runner._store_connect_data(vm_names, self.cred, self.source)
        assert len(self.scan_job.connection_results.task_results.all()) == 1

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
        assert isinstance(vm_names, list) is True
        assert vm_names == ["vm1", "vm2"]

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
                assert vm_names == ["vm1", "vm2", "vm2"]
                mock_vcenter_connect.assert_called_once_with(ANY)
                mock_names.assert_called_once_with(ANY)

    def test_get_result_none(self):
        """Test get result method when no results exist."""
        results = self.scan_task.get_result().systems.first()
        assert results is None

    def test_get_result(self):
        """Test get result method when results exist."""
        conn_result = self.scan_task.connection_result
        results = self.scan_task.get_result()
        assert results == conn_result

    def test_failed_run(self):
        """Test the run method."""
        with patch.object(
            ConnectTaskRunner, "connect", side_effect=invalid_login
        ) as mock_connect:
            status = self.runner.run()
            assert ScanTask.FAILED == status[1]
            mock_connect.assert_called_once_with()

    def test_unreachable_run(self):
        """Test the run method with unreachable."""
        with patch.object(
            ConnectTaskRunner, "connect", side_effect=unreachable_host
        ) as mock_connect:
            status = self.runner.run()
            assert ScanTask.FAILED == status[1]
            mock_connect.assert_called_once_with()

    def test_run(self):
        """Test the run method."""
        with patch.object(
            ConnectTaskRunner, "connect", return_value=["vm1", "vm2"]
        ) as mock_connect:
            status = self.runner.run()
            assert ScanTask.COMPLETED == status[1]
            mock_connect.assert_called_once_with()
