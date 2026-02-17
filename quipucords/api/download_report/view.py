"""View for downloading reports."""

import logging

from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.report.reports_gzip_renderer import ReportsGzipRenderer
from api.views import aggregate_report, deployments, details, reports

logger = logging.getLogger(__name__)


@api_view(["get"])
@renderer_classes((JSONRenderer, ReportsGzipRenderer))
def download_report(request, report_id):
    """Download a report."""
    # Access the underlying Django HttpRequest object
    django_http_request = request._request

    report_type = request.GET.get("report_type", "report")

    print(
        f"\nXXXXXXXXXXXXXXXXXXX\n"
        f" AHA!!! report_type = {report_type}"
        f" for report_id = {report_id}\n"
    )
    match report_type:
        case "report":  # Default tar.gz, same as v1 reports/<report_id>/
            return reports(django_http_request, report_id)
        case "aggregate":
            return aggregate_report(django_http_request, report_id)
        case "deployments":
            return deployments(django_http_request, report_id)
        case "details":
            return details(django_http_request, report_id)
        case _:
            return Response(
                {"error": f"unsupported report_type {report_type} specified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
