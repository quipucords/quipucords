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

    @classmethod
    def kill(cls, job: ScanJob):
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
                f"{cls.log_prefix}: Could not kill the scan job {scan_job_id},"
                " no related Celery Task found"
            )
            return False

        logger.info(
            f"{cls.log_prefix}: Canceling the Celery Task {celery_task_id}"
            f" for scan job {scan_job_id}"
        )
        celery_task = AsyncResult(str(celery_task_id))
        celery_task.revoke()
        return True

    @classmethod
    def put(cls, scan_job_runner: CeleryBasedScanJobRunner):
        """Process the given CeleryBasedScanJobRunner's job and tasks."""
        celery_task_id = scan_job_runner.run()
        scan_job_id = scan_job_runner.scan_job.id
        set_scan_job_celery_task_id(scan_job_id, str(celery_task_id))
        logger.info(
            f"{cls.log_prefix}: Started the Celery Task {celery_task_id}"
            f" for scan job {scan_job_id}"
        )
