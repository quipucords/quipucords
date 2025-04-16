"""View for aggregate report."""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.aggregate_report.model import get_aggregate_report_by_report_id
from api.aggregate_report.serializer import AggregateReportSerializer


@extend_schema(responses=AggregateReportSerializer)
@api_view(["GET"])
def aggregate_report(request, report_id: int) -> Response:
    """Lookup and return an Aggregate Report."""
    aggregate = get_serialized_aggregate_report(report_id)
    if aggregate:
        return Response(aggregate)
    raise NotFound


def get_serialized_aggregate_report(report_id: int) -> AggregateReportSerializer | None:
    """
    Get the aggregate report for the report id specified.

    If the aggregate report does not exist for the report specified,
    it will be created.
    """
    aggregate = get_aggregate_report_by_report_id(report_id)
    if aggregate:
        return AggregateReportSerializer(aggregate).data
    return None
