"""Queue Manager module."""

import logging
from threading import Thread, Timer
from time import sleep

from django.conf import settings
from django.db.models import Q

from api.models import ScanJob, ScanTask
from scanner.job import ScanJobRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

RUN_QUEUE_SLEEP_TIME = 5
SCAN_MANAGER_LOG_PREFIX = "SCAN JOB MANAGER"


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
        logger.warning("Cannot put a job on the scan manager because it is disabled.")


class Manager(Thread):
    """Manager of scan job queue."""

    def __init__(self):
        """Initialize the manager."""
        Thread.__init__(self)
        self.scan_queue = []
        self.current_job_runner = None
        self.terminated_job_runner = None
        self.termination_elapsed_time = 0
        self.running = True
        logger.info("%s: Scan manager instance created.", SCAN_MANAGER_LOG_PREFIX)

    def start_log_timer(self):
        """Start log timer."""
        self.log_info()
        heartbeat = Timer(settings.QUIPUCORDS_MANAGER_HEARTBEAT, self.start_log_timer)
        if self.running:
            heartbeat.start()

    def log_info(self):
        """Log the status of the scan manager."""
        current_scan_job = None
        if self.current_job_runner:
            current_scan_job = self.current_job_runner.identifier
            scan_job_message = f"Currently running scan job {current_scan_job}"
        else:
            scan_job_message = "No scan job currently running"

        scan_queue_ids = [scan_runner.scan_job.id for scan_runner in self.scan_queue]
        scan_queue_ids.reverse()

        logger.info(
            "%s: %s.  Scan queue length is %s. Queued jobs: %s",
            SCAN_MANAGER_LOG_PREFIX,
            scan_job_message,
            len(self.scan_queue),
            scan_queue_ids,
        )

    def work(self):
        """Start to execute scans in the queue."""
        if len(self.scan_queue) > 0:  # pylint: disable=C1801
            self.current_job_runner = self.scan_queue.pop()
            if self.current_job_runner.scan_job.status in [
                ScanTask.PENDING,
                ScanTask.RUNNING,
            ]:
                logger.info(
                    "%s: Loading scan job %s.",
                    SCAN_MANAGER_LOG_PREFIX,
                    self.current_job_runner.scan_job.id,
                )
                self.current_job_runner.start()
                self.log_info()
            else:
                error = (
                    f"{SCAN_MANAGER_LOG_PREFIX}: Could not start job."
                    f" Job was not in {ScanTask.PENDING} state."
                )
                self.current_job_runner.scan_job.log_message(
                    error, log_level=logging.ERROR
                )

    def put(self, job):
        """Add job to scan queue.

        :param job: Job to be performed.
        """
        self.scan_queue.insert(0, job)
        self.log_info()

    # pylint: disable=inconsistent-return-statements
    def kill(self, job, command):
        """Kill a job or remove it from the running queue.

        :param job: The job to kill.
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
                f"{SCAN_MANAGER_LOG_PREFIX}: Send interrupt"
                " to allow job orderly shutdown"
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
            logger.info(
                "%s: Checking scan queue for job to remove.", SCAN_MANAGER_LOG_PREFIX
            )
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
                    SCAN_MANAGER_LOG_PREFIX,
                    job_id,
                )
            else:
                logger.info(
                    "%s: Job %d was not found in the scan queue.",
                    SCAN_MANAGER_LOG_PREFIX,
                    job_id,
                )
            return killed

    def restart_incomplete_scansjobs(self):
        """Look for incomplete scans and restart."""
        logger.info("%s: Searching for incomplete scans", SCAN_MANAGER_LOG_PREFIX)

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
                SCAN_MANAGER_LOG_PREFIX,
                scanjob.id,
                scanjob.status,
                scanjob.scan_type,
            )
            if scanjob.status == ScanTask.CREATED:
                scanjob.queue()
            self.put(scanner)
            restarted_scan_count += 1

        if restarted_scan_count == 0:
            logger.info(
                "%s: No running or pending scan jobs to start", SCAN_MANAGER_LOG_PREFIX
            )

    def run(self):
        """Trigger thread execution."""
        # pylint: disable=too-many-branches
        self.restart_incomplete_scansjobs()
        logger.info("%s: Started run loop.", SCAN_MANAGER_LOG_PREFIX)
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
                        f"{SCAN_MANAGER_LOG_PREFIX}: Process successfully terminated."
                    )
                    self.terminated_job_runner = None
                elif interrupt.value == ScanJob.JOB_TERMINATE_ACK:
                    self.terminated_job_runner.log_message(
                        f"{SCAN_MANAGER_LOG_PREFIX}: Scan job acknowledged"
                        " request to terminate but still processing."
                    )
                else:
                    self.terminated_job_runner.scan_job.log_message(
                        f"{SCAN_MANAGER_LOG_PREFIX}: Scan job has not acknowledged"
                        " request to terminate after"
                        f" {self.termination_elapsed_time:d}s."
                    )

                    # After a time period terminate (will not work in gunicorn)
                    self.termination_elapsed_time += RUN_QUEUE_SLEEP_TIME
                    if (
                        self.termination_elapsed_time
                        == settings.MAX_TIMEOUT_ORDERLY_SHUTDOWN
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
                                f"{SCAN_MANAGER_LOG_PREFIX}:"
                                " scan job has unexpectedly failed."
                            )
                            terminated_job.fail(
                                "Scan manager failed job due to unexpected error."
                            )
                        else:
                            terminated_job.log_message(
                                f"{SCAN_MANAGER_LOG_PREFIX}: scan job has completed."
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
            sleep(RUN_QUEUE_SLEEP_TIME)


def reinitialize():
    """Reinitialize the SCAN_MANAGER module variable."""
    if settings.QPC_DISABLE_THREADED_SCAN_MANAGER:
        manager_class = DisabledManager
    else:
        manager_class = Manager

    global SCAN_MANAGER  # pylint: disable=W0603
    SCAN_MANAGER = manager_class()


SCAN_MANAGER = None
