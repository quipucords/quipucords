"""View for reports."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response

from api.deployments_report.view import build_cached_json_report
from api.models import DeploymentsReport, Report
from api.reports.reports_gzip_renderer import ReportsGzipRenderer
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
    reports_dict = {}
    reports_dict["report_id"] = report_id
    report = get_object_or_404(Report, id=report_id)
    # add scan job id to allow detection of related logs on GzipRenderer
    reports_dict["scan_job_id"] = report.scanjob.id
    serializer = DetailsReportSerializer(report)
    json_details = serializer.data
    json_details.pop("cached_csv", None)
    reports_dict["details_json"] = json_details
    deployments_report = get_object_or_404(DeploymentsReport, report__id=report_id)
    # deployments_report.status seems redundant considering scan job already
    # has a "state machine". Consider removing this in future iterations (we will
    # be forced to revisit this idea when Report replaces Deployments models)
    if deployments_report.status != DeploymentsReport.STATUS_COMPLETE:
        return Response(
            {
                "detail": _(
                    f"Deployment report {report_id} could not be created."
                    " See server logs."
                )
            },
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )
    deployments_json = build_cached_json_report(deployments_report)
    reports_dict["deployments_json"] = deployments_json
    return Response(reports_dict)


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
