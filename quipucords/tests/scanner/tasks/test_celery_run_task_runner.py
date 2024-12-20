"""Test the scanner.tasks.celery_run_task function."""

import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from constants import DataSources
from scanner import tasks
from tests.factories import ScanTaskFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "runner_return_value,expect_success",
    ((ScanTask.COMPLETED, True), (ScanTask.FAILED, False)),
)
def test_celery_run_task_runner(mocker, runner_return_value, expect_success):
    """Test celery_run_task_runner's interactions with related runner functions.

    Since celery_run_task_runner is a relatively simple wrapper for calling other
    functions, this test uses mocks to verify only the expected interactions with those
    other functions: to get and call an appropriate task runner and to return results.
    """
    # Just use known valid types because this test is not focused on unrelated errors.
    scan_type = ScanTask.SCAN_TYPE_CONNECT
    source_type = DataSources.NETWORK
    scan_task = ScanTaskFactory(source__source_type=source_type, scan_type=scan_type)

    mock_get_task_runner_class = mocker.patch.object(tasks, "get_task_runner_class")
    mock_run_task_runner = mocker.patch.object(
        tasks, "run_task_runner", return_value=runner_return_value
    )

    success, scan_task_id, task_status = tasks.celery_run_task_runner.delay(
        scan_task_id=scan_task.id, source_type=source_type, scan_type=scan_type
    ).get()

    mock_get_task_runner_class.assert_called_once_with(source_type, scan_type)
    mock_run_task_runner.assert_called_once_with(
        mock_get_task_runner_class.return_value.return_value
    )
    assert success is expect_success
    assert scan_task_id == scan_task.id
    assert task_status == runner_return_value


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_celery_run_task_runner_canceled(mocker):
    """Test celery_run_task_runner's with scan job canceled."""
    scan_type = ScanTask.SCAN_TYPE_CONNECT
    source_type = DataSources.NETWORK
    scan_task = ScanTaskFactory(source__source_type=source_type, scan_type=scan_type)

    mock_get_task_runner_class = mocker.patch.object(tasks, "get_task_runner_class")
    mocker.patch.object(tasks, "scan_job_is_canceled", return_value=True)

    success, scan_task_id, task_status = tasks.celery_run_task_runner.delay(
        scan_task_id=scan_task.id, source_type=source_type, scan_type=scan_type
    ).get()

    mock_get_task_runner_class.assert_called_once_with(source_type, scan_type)

    assert success is False
    assert scan_task_id == scan_task.id
    assert task_status == ScanTask.CANCELED
