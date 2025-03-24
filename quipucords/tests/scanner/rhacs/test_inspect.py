"""Test RHACS ConnectTaskRunner."""

import logging

import pytest
from requests import ConnectionError
from requests.exceptions import RetryError, TooManyRedirects
from urllib3.exceptions import MaxRetryError

from api.models import ScanTask
from constants import DataSources
from scanner.rhacs.inspect import InspectTaskRunner
from scanner.rhacs.runner import RHACSTaskRunner
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    connect_task = ScanTaskFactory(
        source__source_type=DataSources.RHACS,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
        status=ScanTask.COMPLETED,
        sequence_number=1,
    )
    inspect_task = ScanTaskFactory(
        source=connect_task.source,
        job=connect_task.job,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
    )
    inspect_task.prerequisites.add(connect_task)
    return inspect_task


@pytest.fixture
def mock_client(mocker):
    """Return a mocked RHACS client."""
    return mocker.patch.object(RHACSTaskRunner, "get_client")


@pytest.mark.django_db
def test_connect_successfully(mocker, mock_client, scan_task: ScanTask):
    """Test connecting to RHACS host with success."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.return_value.status_code = 200
    mocker.patch.object(
        runner, "inspect", return_value=[runner.success_message, ScanTask.COMPLETED]
    )
    message, status = runner.execute_task()
    assert message == runner.success_message
    assert status == ScanTask.COMPLETED
    # Next line assumes self.scan_task has type 'inspect'.
    # TODO Delete connect_scan_task when we stop using connect scan tasks.
    connect_scan_task = scan_task.prerequisites.first()
    assert connect_scan_task.systems_count == 1
    assert connect_scan_task.systems_scanned == 1
    assert connect_scan_task.systems_failed == 0
    assert connect_scan_task.systems_unreachable == 0


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
    """Test connecting to RHACS host with failure."""
    caplog.set_level(logging.ERROR)
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.return_value.status_code = err_status
    message, status = runner.execute_task()
    assert message == runner.failure_message
    assert status == ScanTask.FAILED
    # Next line assumes self.scan_task has type 'inspect'.
    # TODO Delete connect_scan_task when we stop using connect scan tasks.
    connect_scan_task = scan_task.prerequisites.first()
    assert connect_scan_task.systems_count == 1
    assert connect_scan_task.systems_scanned == 0
    assert connect_scan_task.systems_failed == 1
    assert connect_scan_task.systems_unreachable == 0
    assert err_message in caplog.text


@pytest.mark.parametrize(
    "exception, unreachable, failed, err_message",
    [
        (
            MaxRetryError("Max retries exceeded", url=None),
            1,
            0,
            "Verify source information and try again.",
        ),
        (
            RetryError("Retry Error"),
            1,
            0,
            "Verify source information and try again.",
        ),
        (
            ConnectionError("Connection Error"),
            1,
            0,
            "Verify source information and try again.",
        ),
        (
            TooManyRedirects("Too many redirects Error"),
            0,
            1,
            "Unexpected exception while handling connection.",
        ),
    ],
)
@pytest.mark.django_db
def test_handling_connection_errors(  # noqa: PLR0913
    mock_client,
    scan_task: ScanTask,
    exception,
    unreachable,
    failed,
    err_message,
    caplog,
):
    """Test handling RHACS connection exceptions."""
    caplog.set_level(logging.ERROR)
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.side_effect = exception
    message, status = runner.execute_task()
    assert message == runner.failure_message
    assert status == ScanTask.FAILED
    # Next line assumes self.scan_task has type 'inspect'.
    # TODO Delete connect_scan_task when we stop using connect scan tasks.
    connect_scan_task = scan_task.prerequisites.first()
    assert connect_scan_task.systems_count == 1
    assert connect_scan_task.systems_scanned == 0
    assert connect_scan_task.systems_failed == failed
    assert connect_scan_task.systems_unreachable == unreachable
    assert err_message in caplog.text
