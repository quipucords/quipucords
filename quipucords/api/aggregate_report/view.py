"""View for aggregate report."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.aggregate_report.model import get_aggregate_report_by_report_id


@api_view(["GET"])
def aggregate_report(request, report_id: int) -> Response:
    """Lookup and return a details system report."""
    return Response(get_aggregate_report_by_report_id(report_id))
