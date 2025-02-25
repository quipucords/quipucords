"""Celery tasks for async DeploymentsReports processes."""

import logging

import celery
from django.db import transaction

logger = logging.getLogger(__name__)


@celery.shared_task()
@transaction.atomic
def generate_cached_fingerprints(deployments_report_id: int):
    """Generate cached fingerprints based on saved SystemFingerprint objects."""
    from api.deployments_report.model import DeploymentsReport, SystemFingerprint

    try:
        from api.deployments_report.serializer import SystemFingerprintSerializer

        deployments_report = DeploymentsReport.objects.get(id=deployments_report_id)
        deployments_report.cached_csv_file_path = None  # cached CSV may now be invalid
        deployments_report.cached_fingerprints = SystemFingerprintSerializer(
            SystemFingerprint.objects.filter(deployment_report=deployments_report),
            many=True,
        ).data
        deployments_report.save()
    except Exception as e:  # noqa: BLE001
        # Catch all exceptions because this Celery task should exit cleanly
        # regardless of whether it succeeds. We might arrive here if the
        # DeploymentsReport no longer exists; maybe it was deleted between when
        # this task was requested and when it executed asynchronously.
        logger.exception(
            "Failed to generate cached fingerprints for DeploymentsReport %s: %s",
            deployments_report_id,
            e,
        )
        return False
    return True


@celery.shared_task()
@transaction.atomic
def generate_and_save_cached_csv(deployments_report_id: int):
    """Generate the save cached csv data for the given deployment report ID."""
    from api.deployments_report.model import DeploymentsReport
    from api.deployments_report.util import create_deployments_csv
    from api.deployments_report.view import build_cached_json_report

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
