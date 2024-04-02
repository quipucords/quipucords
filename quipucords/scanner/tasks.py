"""Celery tasks for running scans."""

import logging

import celery

from api.scanjob.model import ScanJob
from api.scantask.model import ScanTask
from fingerprinter.runner import FingerprintTaskRunner
from scanner.get_scanner import get_scanner
from scanner.job import create_report_for_scan_job, run_task_runner
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)


def get_task_runner_class(source_type, scan_type) -> type[ScanTaskRunner]:
    """Get the ScanTaskRunner class type for the given source and scan types.

    :returns: runner class type (not an instance of the class)
    """
    if scan_type == ScanTask.SCAN_TYPE_CONNECT:
        runner_class_name = "ConnectTaskRunner"
    elif scan_type == ScanTask.SCAN_TYPE_INSPECT:
        runner_class_name = "InspectTaskRunner"
    else:
        logger.exception("invalid scan_type %s", scan_type)
        raise NotImplementedError
    return getattr(get_scanner(source_type), runner_class_name)


@celery.shared_task(bind=True)
def celery_run_task_runner(
    self: celery.Task, scan_task_id: int, source_type: str, scan_type: str
) -> tuple[bool, int, str]:
    """Wrap _celery_run_task_runner to call it as an async Celery task."""
    return _celery_run_task_runner(self, scan_task_id, source_type, scan_type)


def _celery_run_task_runner(
    task_instance: celery.Task, scan_task_id: int, source_type: str, scan_type: str
) -> tuple[bool, int, str]:
    """Run a single ScanTaskRunner.

    :returns: tuple containing success bool, scan task id, and scan task status
    """
    scan_task = ScanTask.objects.get(id=scan_task_id)
    runner_class = get_task_runner_class(source_type, scan_type)
    runner: ScanTaskRunner = runner_class(scan_task.job, scan_task)
    success = (task_status := run_task_runner(runner)) == ScanTask.COMPLETED
    if not success:
        # If this task failed, we do not want subsequent tasks in its chain to run.
        task_instance.request.chain = None
    return success, scan_task_id, task_status


@celery.shared_task
def fingerprint(scan_task_id: int) -> tuple[bool, int, str]:
    """Wrap _fingerprint to call it as an async Celery task."""
    return _fingerprint(scan_task_id)


def _fingerprint(scan_task_id: int) -> tuple[bool, int, str]:
    """Create and assign the Report, and update the related ScanJob status.

    This task should run once after all inspection tasks have collected and stored
    Facts for all Sources associated with the given ScanTask's ScanJob. This logic
    follows the basic pattern established in SyncScanJobRunner.run.

    :returns: tuple containing success bool, scan task id, and scan task status
    """
    # It is safe to assume one will always exist at this point.
    scan_task = ScanTask.objects.get(id=scan_task_id)
    scan_job = scan_task.job

    if not (report := scan_job.report):
        report, error_message = create_report_for_scan_job(scan_job)
        if not report:
            scan_job.status_fail(error_message)
            return False, scan_task_id, ScanTask.FAILED

    # Associate report with the scan job.
    scan_job.report = report
    scan_job.save()

    runner = FingerprintTaskRunner(scan_job, scan_task)
    success = (task_status := run_task_runner(runner)) == ScanTask.COMPLETED
    if success:
        scan_job.log_message(f"Report {scan_job.report_id:d} created.")
    else:
        scan_task.log_message(
            f"Task {scan_task.sequence_number} failed.", log_level=logging.ERROR
        )
        scan_task.log_raw_facts(log_level=logging.ERROR)

    return success, scan_task_id, task_status


@celery.shared_task
def finalize_scan(scan_job_id: int):
    """Wrap _finalize_scan to call it as an async Celery task."""
    return _finalize_scan(scan_job_id)


def _finalize_scan(scan_job_id: int):
    """Set ScanJob status and log failures after running all other ScanJob tasks.

    This logic follows the basic pattern established in SyncScanJobRunner.run.
    """
    scan_job = ScanJob.objects.get(id=scan_job_id)
    failed_tasks = (
        ScanTask.objects.filter(job_id=scan_job_id)
        .exclude(status=ScanTask.COMPLETED)
        .values("id")
    )
    if failed_tasks:
        failed_tasks_ids = [task["id"] for task in failed_tasks]
        error_message = f"The following tasks failed: {failed_tasks_ids}"
        scan_job.status_fail(error_message)
    else:
        scan_job.status_complete()
