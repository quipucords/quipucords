"""Test ACS ConnectTaskRunner."""
import logging

import pytest

from api.models import ScanTask
from constants import DataSources
from scanner.acs.connect import ConnectTaskRunner
from scanner.acs.runner import ACSTaskRunner
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    return ScanTaskFactory(
        source__source_type=DataSources.ACS,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
    )


@pytest.fixture
def mock_client(mocker):
    """Return a mocked ACS client."""
    return mocker.patch.object(ACSTaskRunner, "get_client")


@pytest.mark.django_db
def test_connect_successfully(mock_client, scan_task: ScanTask):
    """Test connecting to ACS host with success."""
    runner = ConnectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.return_value.status_code = 200
    message, status = runner.execute_task(mock_client)
    assert message == runner.success_message
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "err_status, err_message",
    [
        (401, "Authentication failed"),
        (500, "Unexpected status code 500 while connecting"),
    ],
)
def test_connect_with_error(
    mock_client, err_status, err_message, scan_task: ScanTask, caplog
):
    """Test connecting to ACS host with failure."""
    caplog.set_level(logging.ERROR)
    runner = ConnectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.return_value.status_code = err_status
    message, status = runner.execute_task(mock_client)
    assert message == runner.failure_message
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == 1
    assert scan_task.systems_unreachable == 0
    assert err_message in caplog.text
