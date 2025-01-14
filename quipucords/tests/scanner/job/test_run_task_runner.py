"""Tests for scanner.job.run_task_runner."""

import pytest

from api.scantask.model import ScanTask
from scanner import job


@pytest.mark.django_db
def test_run_task_runner_task_fails(mocker, faker):
    """Test run_task_runner sets task and job statuses when the run fails."""
    expected_message = faker.sentence()
    expected_status = ScanTask.FAILED

    mock_runner = mocker.Mock()
    mock_runner.run.return_value = (expected_message, expected_status)
    mock_scan_task = mock_runner.scan_task
    mock_scan_job = mock_runner.scan_job

    runner_status = job.run_task_runner(runner=mock_runner)
    assert runner_status == expected_status
    mock_scan_task.status_fail.assert_called_once_with(expected_message)
    mock_scan_job.status_fail.assert_called_once_with(expected_message)
