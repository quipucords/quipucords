"""View for system reports."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.report_json_gzip_renderer import ReportJsonGzipRenderer
from api.common.util import is_int
from api.deployments_report.csv_renderer import DeploymentCSVRenderer
from api.models import DeploymentsReport

logger = logging.getLogger(__name__)


@api_view(["GET"])
@renderer_classes(
    (JSONRenderer, BrowsableAPIRenderer, DeploymentCSVRenderer, ReportJsonGzipRenderer)
)
def deployments(request, report_id=None):
    """Lookup and return a deployment system report."""
    if not is_int(report_id):
        error = {"report_id": [_(messages.COMMON_ID_INV)]}
        raise ValidationError(error)
    deployments_report, response_status = deployments_report_and_status(report_id)
    return Response(deployments_report, status=response_status)


def deployments_report_and_status(report_id: int) -> tuple[dict, int]:
    """Retrieve a deployment report and related status."""
    deployments_report = get_object_or_404(
        DeploymentsReport.objects.all(), report__id=report_id
    )
    if deployments_report.status != DeploymentsReport.STATUS_COMPLETE:
        return {
            "detail": f"Deployment report {deployments_report.report.id}"
            " could not be created. See server logs."
        }, status.HTTP_424_FAILED_DEPENDENCY

    try:
        deployments_json = build_cached_json_report(deployments_report)
    except FileNotFoundError:
        return {
            "detail": f"Deployment report {deployments_report.report.id}"
            " could not be created. See server logs."
        }, status.HTTP_424_FAILED_DEPENDENCY

    return deployments_json, status.HTTP_200_OK


def build_cached_json_report(deployments_report: DeploymentsReport) -> dict:
    """Create a count report based on the fingerprints and the group.

    :param deployments_report: the DeploymentsReport used to group count
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    system_fingerprints = deployments_report.cached_fingerprints
    return {
        "report_id": deployments_report.report.id,
        "status": deployments_report.status,
        "report_type": deployments_report.report_type,
        "report_version": deployments_report.report_version,
        "report_platform_id": str(deployments_report.report_platform_id),
        "system_fingerprints": system_fingerprints,
    }
