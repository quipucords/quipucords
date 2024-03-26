"""Queue Manager module."""

from __future__ import annotations

import logging
from threading import Thread, Timer
from time import sleep

from celery.result import AsyncResult
from django.conf import settings
from django.db.models import Q

from api.models import ScanJob, ScanTask
from scanner.job import (
    CeleryBasedScanJobRunner,
    ProcessBasedScanJobRunner,
    ScanJobRunner,
)
from scanner.tasks import get_scan_job_celery_task_id, set_scan_job_celery_task_id

logger = logging.getLogger(__name__)


class CeleryScanManager:
    """Drop-in replacement for Manager that uses Celery tasks instead of Processes."""

    log_prefix = "CELERY SCAN MANAGER"

    def __init__(self):
        """Log a warning about this scan manager being incomplete."""
        logger.info("%s: Celery Scan manager instance created.", self.log_prefix)
        logger.warning("%s is not yet fully functional.", __class__.__name__)

    def is_alive(self):
        """Return true to make the common manager interface happy."""
        return True

    def kill(self, job: ScanJob, command: str):
        """Kill a ScanJob Celery task.

        :param job: The ScanJob to kill.
        :param command: string "cancel" or "pause".
        :returns: True if killed, False otherwise.
        """
        scan_job_id = job.id
        job.status = ScanJob.JOB_TERMINATE_CANCEL
        job.status_cancel()
        if job.tasks is not None:
            for scan_task in job.tasks.all():
                scan_task_id = scan_task.id
                task = ScanTask.objects.get(id=scan_task_id)
                task.status = ScanTask.CANCELED
        celery_task_id = get_scan_job_celery_task_id(scan_job_id)
        if celery_task_id is None:
            logger.warning(
                f"{self.log_prefix}: Could not kill the scan job {scan_job_id},"
                " no related Celery Task found"
            )
            return False

        logger.info(
            f"{self.log_prefix}: Canceling the Celery Task {celery_task_id}"
            f" for scan job {scan_job_id}"
        )
        celery_task = AsyncResult(str(celery_task_id))
        celery_task.revoke()
        return True

    def start(self):
        """Return true to make the common manager interface happy."""
        return True

    def put(self, scan_job_runner: CeleryBasedScanJobRunner):
        """Process the given CeleryBasedScanJobRunner's job and tasks."""
        if not isinstance(scan_job_runner, CeleryBasedScanJobRunner):
            raise ValueError(
                "CeleryScanManager only accepts CeleryBasedScanJobRunner runners."
            )
        celery_task_id = scan_job_runner.run()
        scan_job_id = scan_job_runner.scan_job.id
        set_scan_job_celery_task_id(scan_job_id, str(celery_task_id))
        logger.info(
            f"{self.log_prefix}: Started the Celery Task {celery_task_id}"
            f" for scan job {scan_job_id}"
        )


class DisabledManager:
    """Drop-in replacement for Manager that does nothing for development purposes."""

    def is_alive(self):
        """Log a warning message because DisabledManager does nothing."""
        logger.warning("Scan manager is never actually alive because it is disabled.")
        return True

    def kill(self, *args, **kwargs):
        """Log a warning message because DisabledManager does nothing."""
        logger.warning("Cannot kill scan manager because it is disabled.")

    def start(self):
        """Log a warning message because DisabledManager does nothing."""
        logger.warning("Cannot start scan manager because it is disabled.")

    def put(self, *args, **kwargs):
        """Log a warning message because DisabledManager does nothing."""
        logger.warning(
            "Cannot put a scanner on queue because scan manager is disabled."
        )


class Manager(Thread):
    """Manager of scan job queue."""

    run_queue_sleep_time = 5
    log_prefix = "SCAN JOB MANAGER"

    def __init__(self):
        """Initialize the manager."""
        Thread.__init__(self)
        self.scan_queue = []  # type: list[ScanJobRunner]
        self.current_job_runner = None  # type: ScanJobRunner | None
        self.terminated_job_runner = None  # type: ScanJobRunner | None
        self.termination_elapsed_time = 0
        self.running = True
        logger.info("%s: Scan manager instance created.", self.log_prefix)

    def start_log_timer(self):
        """Start log timer."""
        self.log_info()
        heartbeat = Timer(settings.QUIPUCORDS_MANAGER_HEARTBEAT, self.start_log_timer)
        if self.running:
            heartbeat.start()

    def log_info(self):
        """Log the status of the scan manager."""
        if self.current_job_runner:
            current_scan_job = self.current_job_runner.identifier
            scan_job_message = f"Currently running scan job {current_scan_job}"
        else:
            scan_job_message = "No scan job currently running"

        scan_queue_ids = [scan_runner.scan_job.id for scan_runner in self.scan_queue]
        scan_queue_ids.reverse()

        logger.info(
            "%s: %s.  Scan queue length is %s. Queued jobs: %s",
            self.log_prefix,
            scan_job_message,
            len(self.scan_queue),
            scan_queue_ids,
        )

    def work(self):
        """Start to execute scans in the queue."""
        if len(self.scan_queue) > 0:
            self.current_job_runner = self.scan_queue.pop()
            if self.current_job_runner.scan_job.status in [
                ScanTask.PENDING,
                ScanTask.RUNNING,
            ]:
                logger.info(
                    "%s: Loading scan job %s.",
                    self.log_prefix,
                    self.current_job_runner.scan_job.id,
                )
                self.current_job_runner.start()
                self.log_info()
            else:
                error = (
                    f"{self.log_prefix}: Could not start job."
                    f" Job was not in {ScanTask.PENDING} state."
                )
                self.current_job_runner.scan_job.log_message(
                    error, log_level=logging.ERROR
                )

    def put(self, scanner: ScanJobRunner):
        """Add a ScanJobRunner to scan queue.

        :param scanner: ScanJobRunner to run.
        """
        if not isinstance(scanner, ProcessBasedScanJobRunner):
            raise ValueError(
                "Non-multiprocessing ScanJobRunner can't be used alongside thread "
                "based ScanManager."
            )
        self.scan_queue.insert(0, scanner)
        self.log_info()

    def kill(self, job: ScanJob, command: str):
        """Kill a ScanJob or remove it from the running queue.

        :param job: The ScanJob to kill.
        :param command: string "cancel" or "pause".
        :returns: True if killed, False otherwise.
        """
        killed = False
        job_id = job.id
        if (
            self.current_job_runner is not None
            and self.current_job_runner.identifier == job_id
            and self.current_job_runner.is_alive()
        ):
            # record which job is terminated
            self.terminated_job_runner = self.current_job_runner
            self.current_job_runner = None

            job.log_message(
                f"{self.log_prefix}: Send interrupt" " to allow job orderly shutdown"
            )
            if command == "cancel":
                self.terminated_job_runner.manager_interrupt.value = (
                    ScanJob.JOB_TERMINATE_CANCEL
                )
            if command == "pause":
                self.terminated_job_runner.manager_interrupt.value = (
                    ScanJob.JOB_TERMINATE_PAUSE
                )
            self.termination_elapsed_time = 0
        else:
            logger.info("%s: Checking scan queue for job to remove.", self.log_prefix)
            removed = False
            for queued_job in self.scan_queue:
                if queued_job.identifier == job_id:
                    self.scan_queue.remove(queued_job)
                    removed = True
                    self.log_info()
                    break
            if removed:
                killed = True
                logger.info(
                    "%s: Job %d has been removed from the scan queue.",
                    self.log_prefix,
                    job_id,
                )
            else:
                logger.info(
                    "%s: Job %d was not found in the scan queue.",
                    self.log_prefix,
                    job_id,
                )
            return killed

    def restart_incomplete_scansjobs(self):
        """Look for incomplete scans and restart."""
        logger.info("%s: Searching for incomplete scans", self.log_prefix)

        incomplete_scans = ScanJob.objects.filter(
            Q(status=ScanTask.RUNNING)
            | Q(status=ScanTask.PENDING)
            | Q(status=ScanTask.CREATED)
        ).order_by("-status")
        restarted_scan_count = 0
        for scanjob in incomplete_scans:
            scanner = ScanJobRunner(scanjob)
            logger.info(
                "%s: Adding scan job(id=%d, status=%s, scan_type=%s)",
                self.log_prefix,
                scanjob.id,
                scanjob.status,
                scanjob.scan_type,
            )
            if scanjob.status == ScanTask.CREATED:
                scanjob.queue()
            self.put(scanner)
            restarted_scan_count += 1

        if restarted_scan_count == 0:
            logger.info("%s: No running or pending scan jobs to start", self.log_prefix)

    def run(self):  # noqa: PLR0912, C901
        """Trigger thread execution."""
        self.restart_incomplete_scansjobs()
        logger.info("%s: Started run loop.", self.log_prefix)
        self.start_log_timer()
        while self.running:
            queue_len = len(self.scan_queue)
            if self.terminated_job_runner is not None:
                # Occurs when current job was terminated
                killed = not self.terminated_job_runner.is_alive()
                interrupt = self.terminated_job_runner.manager_interrupt
                if killed:
                    # Set this to None so another job can run.
                    self.terminated_job_runner.scan_job.log_message(
                        f"{self.log_prefix}: Process successfully terminated."
                    )
                    self.terminated_job_runner = None
                elif interrupt.value == ScanJob.JOB_TERMINATE_ACK:
                    self.terminated_job_runner.log_message(
                        f"{self.log_prefix}: Scan job acknowledged"
                        " request to terminate but still processing."
                    )
                else:
                    self.terminated_job_runner.scan_job.log_message(
                        f"{self.log_prefix}: Scan job has not acknowledged"
                        " request to terminate after"
                        f" {self.termination_elapsed_time:d}s."
                    )

                    # After a time period terminate (will not work in gunicorn)
                    self.termination_elapsed_time += self.run_queue_sleep_time
                    if (
                        self.termination_elapsed_time
                        >= settings.MAX_TIMEOUT_ORDERLY_SHUTDOWN
                    ):
                        self.terminated_job_runner.scan_job.log_message(
                            "FORCEFUL TERMINATION OF JOB PROCESS"
                        )
                        self.terminated_job_runner.terminate()
            elif self.current_job_runner is not None:
                # Occurs when current jobs ends and at least 1 in queue
                killed = not self.current_job_runner.is_alive()
                if killed:
                    terminated_job = ScanJob.objects.filter(
                        id=self.current_job_runner.scan_job.id
                    ).first()
                    if terminated_job:
                        if terminated_job.status in [
                            ScanTask.PENDING,
                            ScanTask.CREATED,
                            ScanTask.RUNNING,
                        ]:
                            terminated_job.log_message(
                                f"{self.log_prefix}:"
                                " scan job has unexpectedly failed."
                            )
                            terminated_job.status_fail(
                                "Scan manager failed job due to unexpected error."
                            )
                        else:
                            terminated_job.log_message(
                                f"{self.log_prefix}: scan job has completed."
                            )
                    else:
                        self.current_job_runner.scan_job.log_message(
                            "Scan manager detected deletion of scan job "
                            "model before final updates applied."
                        )
                    self.current_job_runner = None
                    if queue_len > 0:
                        self.work()
            elif queue_len > 0 and self.current_job_runner is None:
                # Occurs when no current job, but new one added
                self.work()
            sleep(self.run_queue_sleep_time)


def reinitialize():
    """Reinitialize the SCAN_MANAGER module variable."""
    if settings.QPC_ENABLE_CELERY_SCAN_MANAGER:
        manager_class = CeleryScanManager
    elif settings.QPC_DISABLE_THREADED_SCAN_MANAGER:
        manager_class = DisabledManager
    else:
        manager_class = Manager

    global SCAN_MANAGER  # noqa: PLW0603
    SCAN_MANAGER = manager_class()


SCAN_MANAGER = None
