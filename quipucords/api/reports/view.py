"""View for reports."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.deployments_report.view import build_cached_json_report
from api.models import DeploymentsReport, Report
from api.reports.reports_gzip_renderer import ReportsGzipRenderer
from api.serializers import DetailsReportSerializer
from api.user.authentication import QuipucordsExpiringTokenAuthentication

logger = logging.getLogger(__name__)

auth_classes = (QuipucordsExpiringTokenAuthentication, SessionAuthentication)
perm_classes = (IsAuthenticated,)


@api_view(["GET"])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
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
