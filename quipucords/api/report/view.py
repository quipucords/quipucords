"""Report view."""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from json_agg import JSONObjectAgg
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.aggregate_report.view import get_serialized_aggregate_report
from api.deployments_report.view import get_deployments_report
from api.insights_report.serializers import YupanaPayloadSerializer
from api.insights_report.view import get_report, validate_deployment_report_status
from api.models import DeploymentsReport, InspectResult, Report
from api.report.reports_gzip_renderer import ReportsGzipRenderer
from api.report.serializer import InspectResultSerializer, ReportSerializer
from api.report.view_v1 import get_reports_report
from api.serializers import DetailsReportSerializer

from .mixins import ReportViewMixin


class RawFactsReportView(ReportViewMixin, ListAPIView):
    """RawFacts Report View."""

    report_type = "raw_facts"
    queryset = InspectResult.objects.prefetch_related("inspect_group").annotate(
        raw_facts=JSONObjectAgg("facts__name", "facts__value", sqlite_func="json")
    )
    lookup_field = "inspect_group__reports__id"
    serializer_class = InspectResultSerializer


class ReportFilter(FilterSet):
    """Filter for reports."""

    class Meta:
        """Metadata for filterset."""

        model = Report
        fields = {
            "id": ["exact"],
            "origin": ["exact"],
            "created_at": ["exact", "gt", "gte", "lt", "lte"],
        }


class ReportViewSet(ReadOnlyModelViewSet):
    """A view set for Reports."""

    queryset = Report.objects.select_related("scanjob")
    serializer_class = ReportSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ReportFilter
    ordering_fields = ("id", "origin", "created_at")
    ordering = ("-created_at",)


@api_view(["get"])
@renderer_classes(
    (
        JSONRenderer,
        ReportsGzipRenderer,
    )
)
def download_report(request, report_id):
    """View for downloading a report."""
    report_type = request.GET.get("report_type", "default")

    response_report = None
    response_status = status.HTTP_200_OK

    match report_type:
        case "default":  # Default tar.gz, same as /api/v1/reports/<report_id>/
            response_report, response_status = get_reports_report(report_id)
            if response_status == status.HTTP_200_OK:
                renderer = ReportsGzipRenderer()
                request.accepted_renderer = renderer
                request.accepted_media_type = renderer.media_type
        case "aggregate":  # same as /api/v1/reports/<report_id>/aggregate
            response_report = get_serialized_aggregate_report(report_id)
            if not response_report:
                response_report = dict()
        case "deployments":  # same as /api/v1/reports/<report_id>/deployments
            response_report, response_status = get_deployments_report(report_id)
        case "details":  # same as /api/v1/reports/<report_id>/details
            detail_data = get_object_or_404(Report.objects.all(), id=report_id)
            serializer = DetailsReportSerializer(detail_data)
            response_report = serializer.data
            response_report.pop("cached_csv", None)
        case "insights":  # same as /api/v1/reports/<report_id>/insights
            deployment_report = get_object_or_404(
                DeploymentsReport.objects.only("id", "status"), report__id=report_id
            )
            validate_deployment_report_status(deployment_report)
            report = get_report(deployment_report)
            serializer = YupanaPayloadSerializer(report)
            response_report = serializer.data
        case _:
            return Response(
                {"detail": f"Unsupported report_type {report_type} specified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(response_report, status=response_status)
