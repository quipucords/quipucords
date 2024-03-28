"""Test the scanner.tasks.fingerprint function.

These tests create several objects and patched mocks because of the complex interactions
inside the fingerprint function.
"""

import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from scanner import tasks
from tests.factories import ReportFactory, ScanJobFactory, ScanTaskFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_fingerprint_happy_path_details_report_already_exists(mocker):
    """Test fingerprint calls fingerprint runner when details report already exists."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    report = ReportFactory(scanjob=scan_job)
    scan_task = ScanTaskFactory(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
        status=ScanTask.PENDING,
        job=scan_job,
    )
    mock_run_task_runner = mocker.patch(
        "scanner.tasks.run_task_runner", return_value=ScanTask.COMPLETED
    )
    mock_fingerprint_runner_class = mocker.patch.object(tasks, "FingerprintTaskRunner")
    mock_create_details_report = mocker.patch(
        "scanner.tasks.create_report_for_scan_job"
    )

    success, scan_task_id, status = tasks.fingerprint.delay(scan_task.id).get()
    scan_job.refresh_from_db()
    report.refresh_from_db()

    assert success
    assert scan_task_id == scan_task.id, "unexpected returned scan_task_id"
    assert status == ScanTask.COMPLETED, "unexpected returned status"
    assert scan_job.report == report
    assert mock_fingerprint_runner_class.call_args[0][0].id == scan_job.id
    assert mock_fingerprint_runner_class.call_args[0][1].id == scan_task.id
    mock_fingerprint_runner = mock_fingerprint_runner_class.return_value
    mock_run_task_runner.assert_called_with(mock_fingerprint_runner)
    mock_create_details_report.assert_not_called()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_fingerprint_happy_path_creates_details_report(mocker):
    """Test fingerprint creates missing details report and calls fingerprint runner."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_task = ScanTaskFactory(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, status=ScanTask.PENDING, job=scan_job
    )
    report = ReportFactory(scanjob=scan_job)
    mocker.patch(
        "scanner.tasks.create_report_for_scan_job",
        return_value=(report, None),
    )
    mock_run_task_runner = mocker.patch(
        "scanner.tasks.run_task_runner", return_value=ScanTask.COMPLETED
    )
    mock_fingerprint_runner_class = mocker.patch.object(tasks, "FingerprintTaskRunner")

    success, scan_task_id, status = tasks.fingerprint.delay(scan_task.id).get()
    scan_job.refresh_from_db()
    report.refresh_from_db()

    assert success
    assert scan_task_id == scan_task.id, "unexpected returned scan_task_id"
    assert status == ScanTask.COMPLETED, "unexpected returned status"
    assert scan_job.report == report
    assert mock_fingerprint_runner_class.call_args[0][0].id == scan_job.id
    assert mock_fingerprint_runner_class.call_args[0][1].id == scan_task.id
    mock_fingerprint_runner = mock_fingerprint_runner_class.return_value
    mock_run_task_runner.assert_called_with(mock_fingerprint_runner)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_fingerprint_fails_when_create_details_report_fails(mocker):
    """Test fingerprint fails correctly if creating missing details report fails."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING, report=None)
    scan_task = ScanTaskFactory(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, status=ScanTask.PENDING, job=scan_job
    )
    mocker.patch(
        "scanner.tasks.create_report_for_scan_job", return_value=(None, "fail")
    )
    mock_run_task_runner = mocker.patch("scanner.tasks.run_task_runner")
    mock_fingerprint_runner_class = mocker.patch.object(tasks, "FingerprintTaskRunner")

    success, scan_task_id, status = tasks.fingerprint.delay(scan_task.id).get()
    scan_job.refresh_from_db()

    assert not success
    assert scan_task_id == scan_task.id
    assert status == ScanTask.FAILED
    assert scan_job.report is None
    assert scan_job.report_id is None
    mock_run_task_runner.assert_not_called()
    mock_fingerprint_runner_class.assert_not_called()
