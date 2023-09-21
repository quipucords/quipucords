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
from rest_framework.serializers import ValidationError

from api import messages
from api.common.util import is_int
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
def reports(request, report_id=None):
    """Lookup and return reports."""
    reports_dict = {}
    if report_id is not None:
        if not is_int(report_id):
            error = {"report_id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
    reports_dict["report_id"] = report_id
    # details
    details_data = get_object_or_404(Report.objects.all(), report_id=report_id)
    # add scan job id to allow detection of related logs on GzipRenderer
    reports_dict["scan_job_id"] = details_data.scanjob.id
    serializer = DetailsReportSerializer(details_data)
    json_details = serializer.data
    json_details.pop("cached_csv", None)
    reports_dict["details_json"] = json_details
    # deployments
    deployments_data = get_object_or_404(
        DeploymentsReport.objects.all(), report_id=report_id
    )
    if deployments_data.status != DeploymentsReport.STATUS_COMPLETE:
        deployments_id = deployments_data.details_report.id
        return Response(
            {
                "detail": f"Deployment report {deployments_id} could not be created."
                "  See server logs."
            },
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )
    deployments_report = build_cached_json_report(deployments_data)
    reports_dict["deployments_json"] = deployments_report
    return Response(reports_dict)
