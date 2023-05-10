"""ScanJobRunner runs a group of scan tasks."""

from __future__ import annotations

import logging
from multiprocessing import Process, Value

from django.conf import settings
from django.db.models import Q

from api.common.common_report import create_report_version
from api.details_report.util import (
    build_sources_from_tasks,
    create_details_report,
    validate_details_report_json,
)
from api.models import ScanJob, ScanTask
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
        Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
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


def create_details_report_for_scan_job(scan_job: ScanJob):
    """Create and save a DetailsReport if the ScanJob's ScanTasks have valid Sources.

    :returns: tuple[DetailsReport,str] with the created DetailsReport (if successful)
        and error string (if not successful)
    """
    inspect_tasks = scan_job.tasks.filter(
        scan_type=ScanTask.SCAN_TYPE_INSPECT
    ).order_by("sequence_number")
    sources = build_sources_from_tasks(inspect_tasks.filter(status=ScanTask.COMPLETED))

    if not sources:
        return None, "No connection results found."

    details_report_json = {
        "sources": sources,
        "report_type": "details",
        "report_version": create_report_version(),
    }
    has_errors, validation_result = validate_details_report_json(
        details_report_json, False
    )

    if has_errors:
        return None, f"Scan produced invalid details report JSON: {validation_result}"

    if details_report := create_details_report(
        create_report_version(), details_report_json
    ):
        return details_report, None

    return None, "No facts gathered from scan."


class ScanJobRunner:
    """Proxy class to initialize the proper ScanJobRunner."""

    def __new__(cls, *args, **kwargs) -> SyncScanJobRunner | ProcessBasedScanJobRunner:
        """Initialize the appropriate ScanJobRunner."""
        if settings.QPC_DISABLE_MULTIPROCESSING_SCAN_JOB_RUNNER:
            return SyncScanJobRunner(*args, **kwargs)
        return ProcessBasedScanJobRunner(*args, **kwargs)


class ProcessBasedScanJobRunner(Process):
    """Execute a group of scan tasks in a separate process."""

    def __init__(self, scan_job):
        """Create discovery scanner."""
        super().__init__()
        self.scan_job = scan_job
        self.identifier = scan_job.id
        self.manager_interrupt = Value("i", ScanJob.JOB_RUN)

    def run(self):
        """Trigger process execution."""
        agnostic_runner = SyncScanJobRunner(self.scan_job, self.manager_interrupt)
        return agnostic_runner.start()

    def __str__(self):
        """Convert to string."""
        return f"{{scan_job:{self.scan_job.id}, }}"


class SyncScanJobRunner:
    """Executes a group of tasks bound to a scan_job synchronously."""

    def __init__(self, scan_job: ScanJob, manager_interrupt: Value = None):
        """Create class instance."""
        self.scan_job = scan_job
        self.manager_interrupt = manager_interrupt or Value("i", ScanJob.JOB_RUN)

    def start(self):
        """Execute tasks by calling "run" method."""
        # This method only exists to mimic ProcessBasedScanJobRunner API, which has
        # "start" implemented in its base class.
        return self.run()

    def check_manager_interrupt(self) -> str | None:
        """Check if this job is being interrupted, and handle it if necessary."""
        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            self.scan_job.cancel()
            return ScanTask.CANCELED

        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            self.scan_job.pause()
            return ScanTask.PAUSED

        return None

    def run(self):
        """Execute runner."""
        # pylint: disable=too-many-return-statements,too-many-branches
        if interrupt_status := self.check_manager_interrupt():
            return interrupt_status

        self.scan_job.start()  # Only updates the ScanJob model in the database.
        if self.scan_job.status != ScanTask.RUNNING:
            error_message = (
                "Job could not transition to running state.  See error logs."
            )
            self.scan_job.fail(error_message)
            return ScanTask.FAILED

        task_runners, fingerprint_task_runner = get_task_runners_for_job(self.scan_job)

        failed_tasks = []
        for runner in task_runners:
            task_status = self._run_task(runner)

            if task_status == ScanTask.FAILED:
                # Task did not complete successfully
                failed_tasks.append(runner.scan_task)
            elif task_status != ScanTask.COMPLETED:
                # something went wrong or cancel/pause
                return task_status

        if self.scan_job.scan_type in [
            ScanTask.SCAN_TYPE_INSPECT,
            ScanTask.SCAN_TYPE_FINGERPRINT,
        ]:
            if not (details_report := fingerprint_task_runner.scan_task.details_report):
                details_report, error_message = create_details_report_for_scan_job(
                    self.scan_job
                )
                if not details_report:
                    self.scan_job.fail(error_message)
                    return ScanTask.FAILED

            # Associate details report with scan job
            self.scan_job.details_report = details_report
            self.scan_job.save()

            # Associate details report with fingerprint task
            fingerprint_task_runner.scan_task.details_report = details_report
            fingerprint_task_runner.scan_task.save()
            try:
                task_status = self._run_task(fingerprint_task_runner)
            except Exception as error:
                fingerprint_task_runner.scan_task.log_message(
                    "DETAILS REPORT - "
                    "The following details report failed to generate a"
                    f" deployments report: {details_report}",
                    log_level=logging.ERROR,
                    exception=error,
                )
                raise error
            if task_status in [ScanTask.CANCELED, ScanTask.PAUSED]:
                return task_status
            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully
                failed_tasks.append(fingerprint_task_runner.scan_task)
                fingerprint_task_runner.scan_task.log_message(
                    f"Task {fingerprint_task_runner.scan_task.sequence_number} failed.",
                    log_level=logging.ERROR,
                )
                fingerprint_task_runner.scan_task.log_message(
                    "DETAILS REPORT - "
                    "The following details report failed to generate a"
                    f" deployments report: {details_report}",
                    log_level=logging.ERROR,
                )
            else:
                # Record results for successful tasks
                self.scan_job.report_id = details_report.deployment_report.id
                self.scan_job.save()
                self.scan_job.log_message(
                    f"Report {self.scan_job.report_id:d} created."
                )

        if failed_tasks:
            failed_task_ids = ", ".join(
                [str(task.sequence_number) for task in failed_tasks]
            )
            error_message = f"The following tasks failed: {failed_task_ids}"
            self.scan_job.fail(error_message)
            return ScanTask.FAILED

        self.scan_job.complete()
        return ScanTask.COMPLETED

    def _run_task(self, runner: ScanTaskRunner):
        """Run a single scan task.

        :param runner: ScanTaskRunner
        """
        if interrupt_status := self.check_manager_interrupt():
            return interrupt_status

        runner.scan_task.start()  # Only updates the ScanTask model in the database.
        try:
            status_message, task_status = runner.run(self.manager_interrupt)
        except Exception as error:
            failed_task = runner.scan_task
            context_message = (
                "Unexpected failure occurred. See context below.\n"
                f"SCAN JOB: {self.scan_job}\nTASK: {failed_task}\n"
            )
            if failed_task.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
                creds = [str(cred) for cred in failed_task.source.credentials.all()]
                context_message += (
                    f"SOURCE: {failed_task.source}\nCREDENTIALS: [{creds}]"
                )
            failed_task.fail(context_message)

            message = f"FATAL ERROR. {str(error)}"
            self.scan_job.fail(message)
            raise error

        # Save Task status
        if task_status == ScanTask.CANCELED:
            runner.scan_task.cancel()
            runner.scan_job.cancel()
        elif task_status == ScanTask.PAUSED:
            runner.scan_task.pause()
            runner.scan_job.pause()
        elif task_status == ScanTask.COMPLETED:
            runner.scan_task.complete(status_message)
        elif task_status == ScanTask.FAILED:
            runner.scan_task.fail(status_message)
        else:
            error_message = (
                f"ScanTask {runner.scan_task.sequence_number:d} failed."
                " Scan task must return"
                " ScanTask.COMPLETED or ScanTask.FAILED. ScanTask returned"
                f' "{task_status}" and the following status message: {status_message}'
            )
            runner.scan_task.fail(error_message)
            task_status = ScanTask.FAILED
        return task_status
