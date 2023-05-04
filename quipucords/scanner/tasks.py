"""Celery tasks for running scans."""

import importlib
import logging
from typing import Type

import celery

from api.scanjob.model import ScanJob
from api.scantask.model import ScanTask
from scanner.job import SyncScanJobRunner
from scanner.runner import ScanTaskRunner

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


@celery.shared_task
def run_scan_runner(
    runner_module_name: str, runner_class_name: str, scan_job_id: int, scan_task_id: int
):
    """Run the given ScanTaskRunner for a ScanJob and ScanTask.

    :param runner_module_name: str name of the module containing ScanTaskRunner classes
    :param runner_class_name: str name of the requested ScanTaskRunner class
    :param scan_job_id: int ID of a ScanJob
    :param scan_task_id: int ID of a ScanTask
    """
    # We have to use some direct import here because you can't pass and serialize class
    # types as arguments to Celery tasks.
    module = importlib.import_module(runner_module_name)
    runner_class: Type[ScanTaskRunner] = getattr(module, runner_class_name)
    if not issubclass(runner_class, ScanTaskRunner):
        raise NotImplementedError

    scan_job = ScanJob.objects.get(id=scan_job_id)
    scan_task = ScanTask.objects.get(id=scan_task_id)

    runner = runner_class(scan_job, scan_task)
    status_message, task_status = runner.run()
    logger.info(status_message)
    logger.info(task_status)

    # try:
    #     status_message, task_status = runner.run(self.manager_interrupt)
    # except Exception as error:
    #     failed_task = runner.scan_task
    #     context_message = "Unexpected failure occurred."
    #     context_message += "See context below.\n"
    #     context_message += f"SCAN JOB: {self.scan_job}\n"
    #     context_message += f"TASK: {failed_task}\n"
    #     if failed_task.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
    #         context_message += f"SOURCE: {failed_task.source}\n"
    #         creds = [str(cred) for cred in failed_task.source.credentials.all()]
    #         context_message += f"CREDENTIALS: [{creds}]"
    #     failed_task.fail(context_message)
    #
    #     message = f"FATAL ERROR. {str(error)}"
    #     self.scan_job.fail(message)
    #     raise error
    #
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
