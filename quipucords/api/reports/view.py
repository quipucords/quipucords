from django.db import transaction
from django_filters import NumberFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from api.models import Report, ScanJob, ScanTask
from api.signal.scanjob_signal import start_scan

from .serializer import CreateReportSerializer, ReportOverviewSerializer


class ReportFilter(FilterSet):
    """Filter for ScanJobs."""

    source_id = NumberFilter(field_name="scanjob__sources__id", lookup_expr="exact")
    status = NumberFilter(field_name="scanjob__status", lookup_expr="exact")
    report_id = NumberFilter(field_name="report_platform_id", lookup_expr="exact")

    class Meta:
        """Metadata for filterset."""

        model = Report
        fields = ["source_id", "status", "report_id"]


class ReportViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Report.objects.prefetch_related("scanjob").prefetch_related(
        "scanjob__sources"
    )
    serializer_class = ReportOverviewSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ReportFilter
    ordering_fields = ("id", "status", "start_time", "end_time")
    ordering = ("-id",)

    @extend_schema(request=CreateReportSerializer)
    def create(self, request, *args, **kwargs):
        input_serializer = CreateReportSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            scan_job = ScanJob.objects.create(
                scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                report=Report.objects.create(),
            )
            scan_job.copy_raw_facts(**input_serializer.data)
        start_scan.send(sender="ReportViewSet.create", instance=scan_job)
        serializer = self.get_serializer_class()(scan_job.report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
