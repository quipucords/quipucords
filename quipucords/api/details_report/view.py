"""Viewset for system facts models."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.common_report import create_report_version
from api.common.report_json_gzip_renderer import ReportJsonGzipRenderer
from api.common.util import is_int
from api.details_report.csv_renderer import DetailsCSVRenderer
from api.details_report.util import create_details_report, validate_details_report_json
from api.models import Report, ScanJob, ScanTask
from api.serializers import DetailsReportSerializer
from api.user.authentication import QuipucordsExpiringTokenAuthentication
from scanner.job import ScanJobRunner

logger = logging.getLogger(__name__)

auth_classes = (QuipucordsExpiringTokenAuthentication, SessionAuthentication)
perm_classes = (IsAuthenticated,)


@api_view(["GET"])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes(
    (JSONRenderer, BrowsableAPIRenderer, DetailsCSVRenderer, ReportJsonGzipRenderer)
)
def details(request, report_id=None):
    """Lookup and return a details system report."""
    if report_id is not None:
        if not is_int(report_id):
            error = {"report_id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
    detail_data = get_object_or_404(Report.objects.all(), id=report_id)
    serializer = DetailsReportSerializer(detail_data)
    json_details = serializer.data
    http_accept = request.META.get("HTTP_ACCEPT")
    if http_accept and "text/csv" not in http_accept:
        json_details.pop("cached_csv", None)
    return Response(json_details)


class DetailsReportsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """ModelViewSet to publish system facts.

    This is internal API for a sync way to create a report.
    """

    authentication_classes = (
        QuipucordsExpiringTokenAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    queryset = Report.objects.all()
    serializer_class = DetailsReportSerializer

    def create(self, request, *args, **kwargs):
        """Create a details report."""
        # Validate incoming request body
        has_errors, validation_result = validate_details_report_json(request.data, True)
        if has_errors:
            return Response(validation_result, status=status.HTTP_400_BAD_REQUEST)

        report_version = request.data.get("report_version", None)
        warn_deprecated = False
        if not report_version:
            warn_deprecated = True
            report_version = create_report_version()

        # Create FC model and save data
        report = create_details_report(create_report_version(), request.data)
        scan_job = ScanJob.objects.create(
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, report=report
        )
        if warn_deprecated:
            scan_job.log_message(
                _(messages.FC_MISSING_REPORT_VERSION), log_level=logging.WARNING
            )

        scan_job.queue()
        runner = ScanJobRunner(scan_job)
        runner.run()

        if scan_job.status != ScanTask.COMPLETED:

            error_json = {"error": scan_job.tasks.first().status_message}
            return Response(error_json, status=status.HTTP_400_BAD_REQUEST)

        scan_job = ScanJob.objects.get(pk=scan_job.id)
        report = Report.objects.get(pk=report.id)

        # Prepare REST response body
        serializer = self.get_serializer(report)
        result = serializer.data
        return Response(result, status=status.HTTP_201_CREATED)
