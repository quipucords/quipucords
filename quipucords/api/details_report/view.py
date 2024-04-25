"""Viewset for system facts models."""

import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.report_json_gzip_renderer import ReportJsonGzipRenderer
from api.common.util import is_int
from api.details_report.csv_renderer import DetailsCSVRenderer
from api.models import Report
from api.serializers import DetailsReportSerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
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
