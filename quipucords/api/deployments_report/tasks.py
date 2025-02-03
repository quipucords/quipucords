"""Celery tasks for async DeploymentsReports processes."""

import logging

import celery

from api.deployments_report.model import DeploymentsReport
from api.deployments_report.util import create_deployments_csv
from api.deployments_report.view import build_cached_json_report

logger = logging.getLogger(__name__)


@celery.shared_task()
def generate_and_save_cached_csv(deployments_report_id: int):
    """Generate the save cached csv data for the given deployment report ID."""
    try:
        deployments_report = DeploymentsReport.objects.get(id=deployments_report_id)
        deployments_report.cached_csv_file_path = None
        deployments_report.save()
        deployments_json = build_cached_json_report(deployments_report)
        create_deployments_csv(deployments_json)
    except Exception as e:  # noqa: BLE001
        # Catch all exceptions because this Celery task should exit cleanly
        # regardless of whether it succeeds. We might arrive here if the
        # DeploymentsReport also lacks the cached fingerprints data which
        # is required for building the CSV data.
        logger.exception(e)
        return False
    return True
