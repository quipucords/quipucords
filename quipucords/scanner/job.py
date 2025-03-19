"""ScanJobRunner runs a group of scan tasks."""

from __future__ import annotations

import logging
from collections import defaultdict

import celery
from celery.result import AsyncResult
from django.db.models import Sum

from api.common.common_report import create_report_version
from api.models import ScanJob, ScanTask
from api.reports.model import Report
from fingerprinter.runner import FingerprintTaskRunner
from scanner.get_scanner import get_scanner
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)


def get_task_runner_class(scan_task: ScanTask):
    """Get the appropriate ScanTaskRunner class for the ScanTask."""
    scan_type = scan_task.scan_type
    source_type = scan_task.source.source_type if scan_task.source else None
    if scan_type == ScanTask.SCAN_TYPE_CONNECT:
        scanner = get_scanner(source_type)
        return scanner.ConnectTaskRunner
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        scanner = get_scanner(source_type)
        return scanner.InspectTaskRunner
    if scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
        return FingerprintTaskRunner
    raise NotImplementedError


def get_task_runners_for_job(
    scan_job: ScanJob,
) -> tuple[list[ScanTaskRunner], FingerprintTaskRunner | None]:
    """Get ScanTaskRunners for all the tasks that need to run for this job."""
    incomplete_scan_tasks = scan_job.tasks.filter(
        status__in=[ScanTask.RUNNING, ScanTask.PENDING]
    ).order_by("sequence_number")

    fingerprint_task_runner: FingerprintTaskRunner | None = None
    task_runners: list[ScanTaskRunner] = []

    for scan_task in incomplete_scan_tasks:
        runner_class = get_task_runner_class(scan_task)
        runner = runner_class(scan_job, scan_task)
        if isinstance(runner, FingerprintTaskRunner):
            fingerprint_task_runner = runner
        else:
            task_runners.append(runner)

    scan_job.log_message(f"Job has {len(incomplete_scan_tasks):d} remaining tasks")
    return task_runners, fingerprint_task_runner


def create_report_for_scan_job(scan_job: ScanJob):
    """Create and save a Report if the ScanJob's ScanTasks have valid Sources.

    :returns: tuple[Report,str] with the created Report (if successful)
        and error string (if not successful)
    """
    inspect_query = ScanTask.objects.filter(
        job=scan_job, scan_type=ScanTask.SCAN_TYPE_INSPECT
    ).aggregate(successful_connections=Sum("systems_scanned"))

    if not inspect_query["successful_connections"]:
        return None, "No facts gathered from scan."

    return Report.objects.create(report_version=create_report_version()), None


def run_task_runner(runner: ScanTaskRunner, *run_args):
    """Run a single scan task.

    :param runner: ScanTaskRunner
    """
    runner.scan_task.status_start()  # Only updates the ScanTask model in the database.
    try:
        status_message, task_status = runner.run(*run_args)
    except Exception as error:
        # Note: It should be very unlikely for this exception handling to be triggered.
        # runner.run should already handle *most* exception types, and only a bug or
        # truly unforeseen exception type should end up in here.
        # Some networking errors (host timeout, bad cert) may end up here.
        # TODO Evaluate removing this `except` in favor of higher level error handling.
        failed_task = runner.scan_task
        context_message = (
            "Unexpected failure occurred. See context below.\n"
            f"SCAN JOB: {runner.scan_job}\nTASK: {failed_task}\n"
        )
        if failed_task.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
            creds = [str(cred) for cred in failed_task.source.credentials.all()]
            context_message += f"SOURCE: {failed_task.source}\nCREDENTIALS: [{creds}]"
        failed_task.status_fail(context_message)
        logger.exception(context_message)

        message = f"FATAL ERROR. {str(error)}"
        runner.scan_job.status_fail(message)
        raise error

    # Save Task status
    if task_status == ScanTask.CANCELED:
        runner.scan_task.status_cancel()
        runner.scan_job.status_cancel()
    elif task_status == ScanTask.PAUSED:
        runner.scan_task.status_pause()
        runner.scan_job.status_pause()
    elif task_status == ScanTask.COMPLETED:
        runner.scan_task.status_complete(status_message)
    elif task_status == ScanTask.FAILED:
        runner.scan_task.status_fail(status_message)
        runner.scan_job.status_fail(status_message)
    else:
        error_message = (
            f"ScanTask {runner.scan_task.sequence_number:d} failed."
            " Scan task must return"
            " ScanTask.COMPLETED or ScanTask.FAILED. ScanTask returned"
            f' "{task_status}" and the following status message: {status_message}'
        )
        runner.scan_task.status_fail(error_message)
        task_status = ScanTask.FAILED
    return task_status


class ScanJobRunner:
    """Proxy class to initialize the proper ScanJobRunner."""

    def __new__(cls, *args, **kwargs) -> CeleryBasedScanJobRunner:
        """Initialize the appropriate ScanJobRunner."""
        return CeleryBasedScanJobRunner(*args, **kwargs)


class CeleryBasedScanJobRunner:
    """
    Execute scan tasks for a scan job using Celery workers.

    CeleryBasedScanJobRunner is superficially similar to SyncScanJobRunner, but there
    are several important differences to consider. This scan job runner uses Celery to
    offload processing of scan task work, and it parallelizes that work where possible.
    """

    def __init__(self, scan_job: ScanJob):
        """Initialize the job runner."""
        self.scan_job: ScanJob = scan_job

    def run(self) -> AsyncResult:
        """Prepare this ScanJob's tasks, and request Celery to run them.

        The net result of this method is *similar to* `SyncScanJobRunner.run`, but this
        method returns nothing because it delegates most work to Celery tasks that will
        execute and complete asynchronously.

        Whereas SyncScanJobRunner and ProcessBasedScanJobRunner both work through tasks
        via a linear queue, CeleryBasedScanJobRunner uses Celery to parallelize some of
        the tasks that don't necessarily depend on each other. For a ScanJob that has
        multiple Sources, the ScanTasks may run in parallel for separate Sources. After
        *all* of them have completed, Celery tasks run to fingerprint and store the
        final state of the ScanJob.
        """
        if not self.scan_job.status_start():
            error_message = "ScanJob failed to transition to running state."
            self.scan_job.status_fail(error_message)
            return

        # Import Celery tasks locally to avoid a potential import loop.
        # This is an unfortunate necessity (until future refactoring) because the
        # tasks module also imports from this jobs module.
        from scanner.tasks import (  # pylint: disable=import-outside-toplevel
            celery_run_task_runner,
            finalize_scan,
            fingerprint,
        )

        # Get and group relevant IDs and types for Celery tasks to fetch later.
        incomplete_scan_tasks = self.scan_job.tasks.filter(
            status__in=[ScanTask.RUNNING, ScanTask.PENDING],
            scan_type__in=[ScanTask.SCAN_TYPE_CONNECT, ScanTask.SCAN_TYPE_INSPECT],
        ).order_by("source_id", "sequence_number")
        celery_signatures_by_source = defaultdict(list)
        for scan_task in incomplete_scan_tasks:
            source_id = scan_task.source_id
            scan_task_id = scan_task.id
            source_type = scan_task.source.source_type
            scan_type = scan_task.scan_type
            signature = celery_run_task_runner.si(
                scan_task_id=scan_task_id, source_type=source_type, scan_type=scan_type
            )
            celery_signatures_by_source[source_id].append(signature)

        # Start a chain with a group that contains n chains, one chain for each Source.
        # Each chain contains the tasks required for that Source. Typically, this will
        # contain one "connect" task and one "inspect" task.
        task_chain = celery.group(
            celery.chain(*sigs) for sigs in celery_signatures_by_source.values()
        )

        # Optionally add a link to the chain for fingerprinting.
        # By convention, there should always be 0 or 1 fingerprint ScanTask per ScanJob,
        # and if a fingerprint ScanTask does not exist, it does not need to run.
        if scan_task := ScanTask.objects.filter(
            job__id=self.scan_job.id,
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            status__in=[ScanTask.RUNNING, ScanTask.PENDING],
        ).first():
            task_chain |= fingerprint.si(scan_task_id=scan_task.id)

        # Add a final post-processing task to the chain.
        task_chain |= finalize_scan.si(scan_job_id=self.scan_job.id)
        return task_chain.apply_async()
