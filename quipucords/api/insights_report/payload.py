"""Insights report payload generation."""

import io
import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound

from api import messages
from api.common.entities import ReportEntity
from api.exceptions import FailedDependencyError
from api.insights_report.insights_gzip_renderer import InsightsGzipRenderer
from api.insights_report.serializers import YupanaPayloadSerializer
from api.models import DeploymentsReport, SystemFingerprint

logger = logging.getLogger(__name__)


def validate_deployment_report_status(deployment_report):
    """Check if deployment report did complete."""
    if deployment_report.status != DeploymentsReport.STATUS_COMPLETE:
        raise FailedDependencyError(
            {
                "detail": _(messages.REPORT_INSIGHTS_NOT_CREATED)
                % {"report_id": deployment_report.report.id}
            },
        )


def get_report(deployment_report):
    """Get ReportEntity for deployment_report."""
    try:
        report = ReportEntity.from_report_id(deployment_report.report.id)
    except SystemFingerprint.DoesNotExist as err:
        raise NotFound(
            _(messages.REPORT_INSIGHTS_NOT_GENERATED)
            % {"report_id": deployment_report.report.id}
        ) from err

    return report


def generate_insights_payload(report_id: int) -> dict:
    """Generate the insights report payload dict for the given report ID.

    This is the shared logic used by both the insights API view and the
    publish-to-consoledot Celery task.
    """
    deployment_report = get_object_or_404(
        DeploymentsReport.objects.only("id", "status"), report__id=report_id
    )
    validate_deployment_report_status(deployment_report)
    report_entity = get_report(deployment_report)
    return YupanaPayloadSerializer(report_entity).data


def generate_insights_tarball(report_id: int) -> io.BytesIO:
    """Generate an insights report tarball for the given report ID."""
    payload = generate_insights_payload(report_id)
    return InsightsGzipRenderer().render(payload)
