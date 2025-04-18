"""Celery tasks for running scans."""

import functools
import logging

import celery
from django.conf import settings
from django.core.cache import caches

from api.scanjob.model import ScanJob
from api.scantask.model import ScanTask
from fingerprinter.runner import FingerprintTaskRunner
from quipucords.celery import app as celery_app
from scanner.get_scanner import get_scanner
from scanner.job import create_report_for_scan_job, run_task_runner
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)
celery_inspect = celery_app.control.inspect()


def scan_job_celery_task_id_key(scan_job_id: int):
    """Return the key to store the celery task id for a given scan job id."""
    return f"scan-job-{scan_job_id}-celery-task-id"


def get_scan_job_celery_task_id(scan_job_id: int):
    """Return the celery task id for a given scan job id."""
    return caches["redis"].get(scan_job_celery_task_id_key(scan_job_id))


def set_scan_job_celery_task_id(
    scan_job_id: int, celery_task_id: str, key_timeout=None
):
    """Set the celery task id for the scan job id."""
    if key_timeout is None:
        key_timeout = settings.QUIPUCORDS_SCAN_JOB_TTL
    key = scan_job_celery_task_id_key(scan_job_id)
    caches["redis"].set(key, celery_task_id, key_timeout)


def celery_task_is_revoked(task: celery.Task, celery_task_id: str):
    """Return a boolean if the celery task is specified has been revoked."""
    worker_hostname = task.request.hostname
    revoked_tasks = celery_inspect.revoked()[worker_hostname]
    is_revoked = celery_task_id in revoked_tasks
    return is_revoked


def scan_job_is_canceled(task: celery.Task, scan_job_id: int):
    """Return a boolean indicating if the scan job is cancelled."""
    celery_task_id = get_scan_job_celery_task_id(scan_job_id)
    if celery_task_id is None:
        return False
    return celery_task_is_revoked(task, celery_task_id)


def get_task_runner_class(source_type, scan_type) -> type[ScanTaskRunner]:
    """Get the ScanTaskRunner class type for the given source and scan types.

    :returns: runner class type (not an instance of the class)
    """
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        runner_class_name = "InspectTaskRunner"
    else:
        logger.exception("invalid scan_type %s", scan_type)
        raise NotImplementedError
    return getattr(get_scanner(source_type), runner_class_name)


def set_scan_task_failure_on_exception(func):
    """
    Set the ScanTask's FAILURE status when handling unexpected exceptions.

    This decorator assumes `scan_task_id` will be a keyword argument of the
    function being wrapped.

    Todo: Maybe merge/consolidate this with set_scan_job_failure_on_exception?
    If we merge these two decorators, we probably need a clever way to determine
    whether the relevant object to "fail" is a ScanJob or a ScanTask.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not (scan_task_id := kwargs.get("scan_task_id", None)):
            raise NotImplementedError(
                f"Missing scan_task_id kwarg for decorated function {func.__name__}"
            )
        try:
            return func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            logger.exception(
                f"Unexpected exception in {func.__name__} "
                f"with scan_task_id={scan_task_id}: {e}"
            )
            try:
                scan_task = ScanTask.objects.get(id=scan_task_id)
                scan_task.status_fail(
                    f"Unexpected failure in {func.__name__}. Check logs for details."
                )
            except Exception as e:  # noqa: BLE001
                logger.exception(f"ScanTask({scan_task_id}).status_fail failed: {e}")

    return wrapper


def set_scan_job_failure_on_exception(func):
    """
    Set the ScanJob's FAILURE status when handling unexpected exceptions.

    This decorator assumes `scan_job_id` will be a keyword argument of the
    function being wrapped.

    Todo: Maybe merge/consolidate this with set_scan_task_failure_on_exception?
    If we merge these two decorators, we probably need a clever way to determine
    whether the relevant object to "fail" is a ScanJob or a ScanTask.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not (scan_job_id := kwargs.get("scan_job_id", None)):
            raise NotImplementedError(
                f"Missing scan_job_id kwarg for decorated function {func.__name__}"
            )
        try:
            return func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            logger.exception(
                f"Unexpected exception in {func.__name__} "
                f"with scan_job_id={scan_job_id}: {e}"
            )
            try:
                scan_task = ScanJob.objects.get(id=scan_job_id)
                scan_task.status_fail(
                    f"Unexpected failure in {func.__name__}. Check logs for details."
                )
            except Exception as e:  # noqa: BLE001
                logger.exception(f"ScanJob({scan_job_id}).status_fail failed: {e}")

    return wrapper


@celery.shared_task(bind=True)
@set_scan_task_failure_on_exception
def celery_run_task_runner(
    self: celery.Task, *, scan_task_id: int, source_type: str, scan_type: str
) -> tuple[bool, int, str]:
    """Wrap _celery_run_task_runner to call it as an async Celery task."""
    return _celery_run_task_runner(
        task_instance=self,
        scan_task_id=scan_task_id,
        source_type=source_type,
        scan_type=scan_type,
    )


def _celery_run_task_runner(
    *, task_instance: celery.Task, scan_task_id: int, source_type: str, scan_type: str
) -> tuple[bool, int, str]:
    """Run a single ScanTaskRunner.

    :returns: tuple containing success bool, scan task id, and scan task status
    """
    scan_task = ScanTask.objects.get(id=scan_task_id)
    runner_class = get_task_runner_class(source_type, scan_type)
    runner: ScanTaskRunner = runner_class(scan_task.job, scan_task)
    scan_job_id = scan_task.job.id

    if scan_job_is_canceled(task_instance, scan_job_id):
        logger.info(
            f"Scan Job {scan_job_id} canceled, skipping scan task {scan_task_id}."
        )
        success = False
        task_status = ScanTask.CANCELED
    else:
        success = (task_status := run_task_runner(runner)) == ScanTask.COMPLETED
    if not success:
        # If this task failed, we do not want subsequent tasks in its chain to run.
        task_instance.request.chain = None
    return success, scan_task_id, task_status


@celery.shared_task(bind=True)
@set_scan_task_failure_on_exception
def fingerprint(self: celery.Task, *, scan_task_id: int) -> tuple[bool, int, str]:
    """Wrap _fingerprint to call it as an async Celery task."""
    return _fingerprint(self=self, scan_task_id=scan_task_id)


def _fingerprint(self: celery.Task, *, scan_task_id: int) -> tuple[bool, int, str]:
    """Create and assign the Report, and update the related ScanJob status.

    This task should run once after all inspection tasks have collected and stored
    Facts for all Sources associated with the given ScanTask's ScanJob. This logic
    follows the basic pattern established in SyncScanJobRunner.run.

    :returns: tuple containing success bool, scan task id, and scan task status
    """
    # It is safe to assume one will always exist at this point.
    scan_task = ScanTask.objects.get(id=scan_task_id)
    scan_job = scan_task.job

    if scan_job_is_canceled(self, scan_job.id):
        logger.info(f"Scan Job {scan_job.id} canceled, skipping fingerprint")
        scan_job.status_cancel()
        return False, scan_task_id, ScanTask.CANCELED

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


@celery.shared_task(bind=True)
@set_scan_job_failure_on_exception
def finalize_scan(self: celery.Task, *, scan_job_id: int):
    """Wrap _finalize_scan to call it as an async Celery task."""
    return _finalize_scan(self=self, scan_job_id=scan_job_id)


def _finalize_scan(self: celery.Task, scan_job_id: int):
    """Set ScanJob status and log failures after running all other ScanJob tasks.

    This logic follows the basic pattern established in SyncScanJobRunner.run.
    """
    scan_job = ScanJob.objects.get(id=scan_job_id)
    if scan_job_is_canceled(self, scan_job.id):
        logger.info(f"Scan Job {scan_job_id} canceled, skipping finalize_scan")
        scan_job.status_cancel()
        return

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
