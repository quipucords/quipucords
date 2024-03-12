"""View for system reports."""
import logging

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.exceptions import NotFound
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from api.common.entities import ReportEntity
from api.exceptions import FailedDependencyError
from api.insights_report.insights_gzip_renderer import InsightsGzipRenderer
from api.insights_report.serializers import YupanaPayloadSerializer
from api.models import DeploymentsReport, SystemFingerprint

logger = logging.getLogger(__name__)


@api_view(["GET"])
@renderer_classes((JSONRenderer, InsightsGzipRenderer, BrowsableAPIRenderer))
def insights(request, report_id=None):
    """Lookup and return an Insights system report."""
    deployment_report = get_object_or_404(
        DeploymentsReport.objects.only("id", "status"), report__id=report_id
    )
    _validate_deployment_report_status(deployment_report)
    report = _get_report(deployment_report)
    serializer = YupanaPayloadSerializer(report)
    return Response(serializer.data)


def _validate_deployment_report_status(deployment_report):
    if deployment_report.status != DeploymentsReport.STATUS_COMPLETE:
        raise FailedDependencyError(
            {
                "detail": f"Insights report {deployment_report.report.id} could not be "
                "created. See server logs."
            },
        )


def _get_report(deployment_report):
    try:
        report = ReportEntity.from_report_id(deployment_report.report.id)
    except SystemFingerprint.DoesNotExist as err:
        raise NotFound(
            f"Insights report {deployment_report.report.id} was not generated because "
            "there were 0 valid hosts. See server logs."
        ) from err

    return report
