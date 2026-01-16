"""Report view."""

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from json_agg import JSONObjectAgg
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.models import InspectResult, Report
from api.report.serializer import InspectResultSerializer, ReportSerializer

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
