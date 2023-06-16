"""Test the scanner.tasks.finalize_scan function."""
import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from scanner import tasks
from tests.factories import ScanJobFactory, ScanTaskFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_completed_if_all_tasks_are_completed():
    """Test finalize_scan sets expected COMPLETED status if all tasks are COMPLETED."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    tasks.finalize_scan.delay(scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


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
    tasks.finalize_scan.delay(scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_failed_if_any_task_failed():
    """Test finalize_scan sets expected FAILED status if any task failed."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    ScanTaskFactory(status=ScanTask.FAILED, job=scan_job)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    tasks.finalize_scan.delay(scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED
