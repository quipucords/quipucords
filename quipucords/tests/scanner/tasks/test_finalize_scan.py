"""Test the scanner.tasks.finalize_scan function."""

import logging

import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from scanner import tasks
from tests.factories import ScanJobFactory, ScanTaskFactory


def log_task_ids(tasks):
    """Format tasks ids as they will appear in log message."""
    task_ids = ", ".join(str(t.id) for t in tasks)
    return f"[{task_ids}]"


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_all_complete(caplog):
    """Test finalize_scan sets job status COMPLETED if all tasks are COMPLETED."""
    caplog.set_level(logging.DEBUG, logger="scanner.tasks")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_tasks = [
        ScanTaskFactory(
            scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED
        ),
        ScanTaskFactory(
            scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED
        ),
    ]
    scan_job.tasks.add(*scan_tasks)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED
    log_message = (
        f"Scan Job {scan_job.id} finalize_scan status "
        f"{ScanTask.COMPLETED} tasks: {log_task_ids(scan_tasks)}"
    )
    assert log_message in caplog.messages


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_all_failed(caplog):
    """Test finalize_scan sets job status FAILED if all tasks are FAILED."""
    caplog.set_level(logging.DEBUG, logger="scanner.tasks")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_tasks = [
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.FAILED),
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.FAILED),
    ]
    scan_job.tasks.add(*scan_tasks)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED
    log_message = (
        f"Scan Job {scan_job.id} finalize_scan status "
        f"{ScanTask.FAILED} tasks: {log_task_ids(scan_tasks)}"
    )
    assert log_message in caplog.messages


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_all_canceled(caplog):
    """Test finalize_scan sets job status CANCELED if all tasks are CANCELED."""
    caplog.set_level(logging.DEBUG, logger="scanner.tasks")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_tasks = [
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.CANCELED),
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.CANCELED),
    ]
    scan_job.tasks.add(*scan_tasks)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.CANCELED
    log_message = (
        f"Scan Job {scan_job.id} finalize_scan status "
        f"{ScanTask.CANCELED} tasks: {log_task_ids(scan_tasks)}"
    )
    assert log_message in caplog.messages


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_all_running(caplog):
    """Test finalize_scan sets job status FAILED if all tasks are RUNNING."""
    caplog.set_level(logging.DEBUG, logger="scanner.tasks")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_tasks = [
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.RUNNING),
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.RUNNING),
    ]
    scan_job.tasks.add(*scan_tasks)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED
    log_message = (
        f"Scan Job {scan_job.id} finalize_scan status "
        f"{ScanTask.RUNNING} tasks: {log_task_ids(scan_tasks)}"
    )
    assert log_message in caplog.messages


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_any_complete(caplog):
    """Test finalize_scan sets job status COMPLETE if any task is COMPLETE."""
    caplog.set_level(logging.DEBUG, logger="scanner.tasks")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_tasks = [
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.RUNNING),
        ScanTaskFactory(
            scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED
        ),
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.FAILED),
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.CANCELED),
    ]
    scan_job.tasks.add(*scan_tasks)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED
    for scan_task in scan_tasks:
        log_message = (
            f"Scan Job {scan_job.id} finalize_scan status "
            f"{scan_task.status} tasks: {log_task_ids([scan_task])}"
        )
        assert log_message in caplog.messages


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_completed_even_if_no_tasks_exist():
    """
    Test finalize_scan sets expected COMPLETED status if no tasks exist.

    This is exercising a possibly unexpected edge case with our existing scan job logic
    that we preserved when we wrote finalize_scan. If a task exists with not-COMPLETED
    status, the job fails. Otherwise, it succeeds even if the job has zero tasks.
    A scan with zero tasks reaching this part of the process *probably* never actually
    happens in practice, but since our code technically allows it, I'm defining this
    test so we know if/when this behavior changes.
    """
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)

    tasks.finalize_scan.delay(scan_job_id=scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED
