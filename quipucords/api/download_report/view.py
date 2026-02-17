"""View for downloading reports."""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.aggregate_report.view import get_serialized_aggregate_report
from api.deployments_report.view import get_deployments_report
from api.models import Report
from api.report.reports_gzip_renderer import ReportsGzipRenderer
from api.report.view_v1 import get_reports_report
from api.serializers import DetailsReportSerializer

logger = logging.getLogger(__name__)


@api_view(["get"])
@renderer_classes(
    (
        JSONRenderer,
        ReportsGzipRenderer,
    )
)
def download_report(request, report_id):
    """Download a report."""
    report_type = request.GET.get("report_type", "default")

    match report_type:
        case "default":  # Default tar.gz, same as v1 reports/<report_id>/
            reports_report, response_status = get_reports_report(report_id)
            if response_status == status.HTTP_200_OK:
                renderer = ReportsGzipRenderer()
                request.accepted_renderer = renderer
                request.accepted_media_type = renderer.media_type
            return Response(reports_report, status=response_status)
        case "aggregate":  # same as v1 reports/<report_id>/aggregate
            aggregate = get_serialized_aggregate_report(report_id)
            if aggregate:
                return Response(aggregate)
            return None
        case "deployments":  # same as v1 reports/<report_id>/deployments
            deployments_report, response_status = get_deployments_report(report_id)
            return Response(deployments_report, status=response_status)
        case "details":  # same as v1 reports/<report_id>/details
            detail_data = get_object_or_404(Report.objects.all(), id=report_id)
            serializer = DetailsReportSerializer(detail_data)
            details_report = serializer.data
            details_report.pop("cached_csv", None)
            return Response(details_report)

        case _:
            return Response(
                {"detail": f"Unsupported report_type {report_type} specified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
