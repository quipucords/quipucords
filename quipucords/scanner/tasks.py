"""Celery tasks for running scans."""

import logging

import celery

from api.scanjob.model import ScanJob
from api.scantask.model import ScanTask
from scanner.job import SyncScanJobRunner

logger = logging.getLogger(__name__)


@celery.shared_task
def run_scan_job_runner(scan_job_id: int):
    """
    Run the ScanJobRuner for the given scan_job_id if it needs running.

    This code was originally lifted and adapted from ``scanner.manager.Manager.work``,
    and it's only an initial proof of concept. At the time of this writing, some scan
    tasks may fail catastrophically in Celery because underlying layers still rely on
    multiprocessing, but daemonized processes cannot fork ("daemonic processes are not
    allowed to have children"). More work is needed before we can really use this.
    """
    scan_job = ScanJob.objects.get(id=scan_job_id)
    scan_job_runner = SyncScanJobRunner(scan_job)

    if scan_job.status in [ScanTask.PENDING, ScanTask.RUNNING]:
        logger.info("Loading scan job %s.", scan_job_id)
        scan_job_runner.run()
    else:
        error = f"Could not start job. Job was not in {ScanTask.PENDING} state."
        scan_job_runner.scan_job.log_message(error, log_level=logging.ERROR)
