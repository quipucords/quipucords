"""Test Ansible InspectTaskRunner."""

import pytest

from api.models import ScanTask
from constants import DataSources
from scanner.ansible.exceptions import AnsibleApiDetectionError
from scanner.ansible.inspect import InspectTaskRunner
from scanner.ansible.runner import AnsibleTaskRunner
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    inspect_task = ScanTaskFactory(
        source__source_type=DataSources.ANSIBLE,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        sequence_number=1,
    )
    return inspect_task


@pytest.fixture
def mock_client(mocker):
    """Return a mocked Ansible client."""
    return mocker.patch.object(AnsibleTaskRunner, "get_client")


@pytest.fixture
def test_api_endpoints():
    """Return a mocked set of Ansible API endpoints."""
    return InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/test/v2/me",
        ping="/api/test/v2/ping",
        hosts="/api/test/v2/hosts",
        jobs="/api/test/v2/jobs",
    )


@pytest.mark.django_db
def test_detect_ansible_endpoints_does_not_requery_api(
    mocker, mock_client, test_api_endpoints, scan_task: ScanTask
):
    """Test Detecting Ansible endpoints does not re-query API."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client
    mocker.patch.object(
        runner, "inspect", return_value=[runner.success_message, ScanTask.COMPLETED]
    )
    runner.endpoints = test_api_endpoints
    runner._detect_ansible_endpoints()
    assert not mock_client.assert_called_once()
    assert runner.endpoints.me == "/api/test/v2/me"


@pytest.mark.django_db
def test_check_connection_handles_api_detection_error(
    mocker, mock_client, test_api_endpoints, scan_task: ScanTask
):
    """Test that check_connection handles API detection errors."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client
    runner._detect_ansible_endpoints = mocker.Mock(side_effect=AnsibleApiDetectionError)
    mocker.patch.object(
        runner, "inspect", return_value=[runner.success_message, ScanTask.COMPLETED]
    )
    runner.endpoints = test_api_endpoints
    failure_message, status = runner.check_connection()
    assert not mock_client.assert_called_once()
    assert status == ScanTask.FAILED
