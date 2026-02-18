"""View for reports."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.aggregate_report.view import get_serialized_aggregate_report
from api.deployments_report.view import build_cached_json_report
from api.exceptions import FailedDependencyError
from api.insights_report.serializers import YupanaPayloadSerializer
from api.insights_report.view import get_report as get_lightspeed_report
from api.insights_report.view import validate_deployment_report_status
from api.models import DeploymentsReport, Report
from api.report.reports_gzip_renderer import ReportsGzipRenderer
from api.serializers import (
    DetailsReportSerializer,
    ReportUploadSerializer,
    SimpleScanJobSerializer,
)
from api.signal.scanjob_signal import start_scan

logger = logging.getLogger(__name__)


@api_view(["GET"])
@renderer_classes((ReportsGzipRenderer,))
def reports(request, report_id):
    """Lookup and return reports."""
    reports_report, response_status = reports_report_and_status(report_id)
    return Response(reports_report, status=response_status)


def reports_report_and_status(report_id) -> tuple[dict, int]:
    """Get the reports for a report id and related status."""
    reports_dict = dict()
    reports_dict["report_id"] = report_id
    report = get_object_or_404(Report, id=report_id)
    # add scan job id to allow detection of related logs on GzipRenderer
    reports_dict["scan_job_id"] = report.scanjob.id
    serializer = DetailsReportSerializer(report)
    json_details = serializer.data
    json_details.pop("cached_csv", None)
    reports_dict["details_json"] = json_details
    deployments_report = get_object_or_404(DeploymentsReport, report__id=report_id)
    if deployments_report.status != DeploymentsReport.STATUS_COMPLETE:
        return (
            {
                "detail": _(
                    f"Deployment report {report_id} could not be created."
                    " See server logs."
                )
            },
            status.HTTP_424_FAILED_DEPENDENCY,
        )
    deployments_json = build_cached_json_report(deployments_report)
    reports_dict["deployments_json"] = deployments_json
    aggregate_json = get_serialized_aggregate_report(report_id)
    reports_dict["aggregate_json"] = aggregate_json
    try:
        validate_deployment_report_status(deployments_report)
        lightspeed_report = get_lightspeed_report(deployments_report)
        lightspeed_serializer = YupanaPayloadSerializer(lightspeed_report)
        reports_dict["lightspeed_report"] = lightspeed_serializer.data
    except (FailedDependencyError, NotFound):
        logger.info(
            (
                "Could not generate Lightspeed report for deployment report %s; "
                "skipping\nException that generated this message:"
            ),
            report_id,
            exc_info=True,
        )
    return reports_dict, status.HTTP_200_OK


@api_view(["POST"])
def upload_raw_facts(request):
    """Dedicated view for uploading reports."""
    input_serializer = ReportUploadSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)
    report = input_serializer.save()
    # start fingerprint job
    start_scan.send(sender=__name__, instance=report.scanjob)
    output_serializer = SimpleScanJobSerializer(report.scanjob)
    return Response(output_serializer.data, status=status.HTTP_201_CREATED)
