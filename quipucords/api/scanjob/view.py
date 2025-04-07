"""Scanjob related views."""

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from api.models import ScanJob
from api.scanjob.serializer import ScanJobSerializerV2


class ScanJobFilter(FilterSet):
    """Filter for ScanJobs."""

    class Meta:
        """Metadata for filterset."""

        model = ScanJob
        fields = {
            "status": ["exact"],
            "scan_type": ["exact"],
            "scan_id": ["exact", "isnull"],
            "report_id": ["exact"],
        }


class ScanJobViewSet(viewsets.ReadOnlyModelViewSet):
    """A viewset for ScanJobs."""

    queryset = ScanJob.objects.prefetch_related("sources").with_counts()
    serializer_class = ScanJobSerializerV2
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ScanJobFilter
    ordering_fields = ("id", "scan_type", "status", "start_time", "end_time")
    ordering = ("-id",)
