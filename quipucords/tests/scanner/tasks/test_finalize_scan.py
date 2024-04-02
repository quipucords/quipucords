"""Test the scanner.tasks.finalize_scan function."""

import logging

import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from scanner import tasks
from tests.factories import ScanJobFactory, ScanTaskFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_none_failed():
    """Test finalize_scan sets job status COMPLETED if all tasks are COMPLETED."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    scan_job.tasks.add(
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_CONNECT, status=ScanTask.COMPLETED)
    )
    scan_job.tasks.add(
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED)
    )

    tasks.finalize_scan.delay(scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_some_failed(caplog):
    """Test finalize_scan sets job status FAILED if any task is not COMPLETED."""
    caplog.set_level(logging.ERROR, logger="api.scanjob.model")
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    running_task = ScanTaskFactory(
        scan_type=ScanTask.SCAN_TYPE_CONNECT, status=ScanTask.RUNNING
    )
    scan_job.tasks.add(running_task)
    scan_job.tasks.add(
        ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED)
    )

    tasks.finalize_scan.delay(scan_job.id).get()

    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED
    assert f"The following tasks failed: [{running_task.id}]" in caplog.messages[0]
