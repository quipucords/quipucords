"""Report view."""

from json_agg import JSONObjectAgg
from rest_framework.generics import ListAPIView

from api.models import InspectResult
from api.report.serializer import InspectResultSerializer

from .mixins import ReportViewMixin


class RawFactsReportView(ReportViewMixin, ListAPIView):
    """RawFacts Report View."""

    report_type = "raw_facts"
    queryset = InspectResult.objects.prefetch_related("inspect_group").annotate(
        raw_facts=JSONObjectAgg("facts__name", "facts__value", sqlite_func="json")
    )
    lookup_field = "inspect_group__reports__id"
    serializer_class = InspectResultSerializer
