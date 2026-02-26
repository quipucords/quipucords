"""Report view."""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from json_agg import JSONObjectAgg
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api import messages
from api.aggregate_report.view import (
    AggregateReportSerializer,
    get_serialized_aggregate_report,
)
from api.deployments_report.view import deployments_report_and_status
from api.insights_report.view import get_report, validate_deployment_report_status
from api.models import DeploymentsReport, InspectResult, Report
from api.report.reports_gzip_renderer import ReportsGzipRenderer
from api.report.serializer import InspectResultSerializer, ReportSerializer
from api.report.view_v1 import reports_report_and_status
from api.serializers import (
    DeploymentReportSerializer,
    DetailsReportSerializer,
    YupanaPayloadSerializer,
)

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


# Report type choices for the report download API endpoint
REPORT_TYPE_CHOICES = ["aggregate", "deployments", "details", "insights"]


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="report_type",
            type=OpenApiTypes.STR,
            enum=REPORT_TYPE_CHOICES,
            description="The optional JSON report type to download",
            required=False,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={
        (200, "application/gzip"): OpenApiResponse(
            description="Gzipped Reports archive for the Report specified",
            response=OpenApiTypes.BINARY,
        ),
        ("200_aggregate", "application/json"): OpenApiResponse(
            description="Aggregate Report JSON for the Report specified",
            response=AggregateReportSerializer,
        ),
        ("200_deployments", "application/json"): OpenApiResponse(
            description="Deployments Report JSON for the Report specified",
            response=DeploymentReportSerializer,
        ),
        ("200_details", "application/json"): OpenApiResponse(
            description="Details Reports JSON for the Report specified",
            response=DetailsReportSerializer,
        ),
        ("200_insights", "application/json"): OpenApiResponse(
            description="Insights Reports JSON for the Report specified",
            response=YupanaPayloadSerializer,
        ),
    },
)
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
        case "default":  # v2 of /api/v1/reports/<report_id>/, defaults to tar.gz
            response_report, response_status = reports_report_and_status(report_id)
            # Since DRF Views use the first renderer if selectable via content
            # negotiation, and we want to render the tar.gz by default, we need to
            # check for the default Accept (anything) header and select the
            # Gzip renderer in that case.
            accept_all = "*/*"
            accept_header = request.headers.get("Accept", accept_all)
            if response_status == status.HTTP_200_OK and accept_all in accept_header:
                renderer = ReportsGzipRenderer()
                request.accepted_renderer = renderer
                request.accepted_media_type = renderer.media_type
        case "aggregate":  # v2 of /api/v1/reports/<report_id>/aggregate
            response_report = get_serialized_aggregate_report(report_id)
            if response_report is None:
                return Response(
                    {
                        "detail": _(messages.REPORT_AGGREGATE_NOT_AVAILABLE)
                        % {"report_id": report_id},
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        case "deployments":  # v2 of /api/v1/reports/<report_id>/deployments
            response_report, response_status = deployments_report_and_status(report_id)
        case "details":  # v2 of /api/v1/reports/<report_id>/details
            detail_data = get_object_or_404(Report.objects.all(), id=report_id)
            serializer = DetailsReportSerializer(detail_data)
            response_report = serializer.data
            response_report.pop("cached_csv", None)
        case "insights":  # v2 of /api/v1/reports/<report_id>/insights
            deployment_report = get_object_or_404(
                DeploymentsReport.objects.only("id", "status"), report__id=report_id
            )
            validate_deployment_report_status(deployment_report)
            report = get_report(deployment_report)
            serializer = YupanaPayloadSerializer(report)
            response_report = serializer.data
        case _:
            return Response(
                {
                    "detail": _(messages.REPORT_UNSUPPORTED_REPORT_TYPE)
                    % {"report_type": report_type}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(response_report, status=response_status)
