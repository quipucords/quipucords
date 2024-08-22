"""
Scan manager module.

SCAN_MANAGER acts as a global singleton, but this is just a vestigial artifact
of an older design that required a singleton. SCAN_MANAGER and the general concept
of the "scan manager" may be removed in an upcoming iteration of this code.
"""

from __future__ import annotations

import logging

from celery.result import AsyncResult

from api.models import ScanJob, ScanTask
from scanner.job import CeleryBasedScanJobRunner
from scanner.tasks import get_scan_job_celery_task_id, set_scan_job_celery_task_id

logger = logging.getLogger(__name__)


class CeleryScanManager:
    """Drop-in replacement for Manager that uses Celery tasks instead of Processes."""

    log_prefix = "CELERY SCAN MANAGER"

    def __init__(self):
        """Log a when a new instance is initialized."""
        logger.debug("%s: Celery Scan manager instance created.", self.log_prefix)

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


def reinitialize():
    """Reinitialize the SCAN_MANAGER module variable."""
    manager_class = CeleryScanManager
    global SCAN_MANAGER  # noqa: PLW0603
    SCAN_MANAGER = manager_class()


SCAN_MANAGER = None
