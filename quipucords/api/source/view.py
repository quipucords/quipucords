"""Describes the views associated with the API models."""

from itertools import groupby

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import (
    ALL_IDS_MAGIC_STRING,
    expand_scanjob_with_times,
    is_int,
    set_of_ids_or_all_str,
)
from api.filters import ListFilter
from api.models import Scan, ScanJob, Source
from api.serializers import SourceSerializerV1, SourceSerializerV2
from api.source.util import expand_credential

IDENTIFIER_KEY = "id"
NAME_KEY = "name"


def format_source(json_source):
    """Format source with credentials and most recent connection scan.

    :param json_source: JSON source data from serializer
    :returns: JSON data
    """
    expand_credential(json_source)
    conn_job_id = json_source.pop("most_recent_connect_scan", None)
    if conn_job_id:
        scan_job = ScanJob.objects.get(pk=conn_job_id)

        json_scan_job = expand_scanjob_with_times(scan_job)
        source_id = json_source.get("id")
        task_for_source = scan_job.tasks.filter(source=source_id).first()

        if task_for_source is not None:
            json_scan_job["source_task_id"] = task_for_source.id
            json_scan_job["source_task_status"] = task_for_source.status
            json_scan_job["source_systems_count"] = task_for_source.systems_count
            json_scan_job["source_systems_scanned"] = task_for_source.systems_scanned
            json_scan_job["source_systems_failed"] = task_for_source.systems_failed
            json_scan_job["source_systems_unreachable"] = (
                task_for_source.systems_unreachable
            )

        json_source["connection"] = json_scan_job
    return json_source


class SourceFilter(FilterSet):
    """Filter for sources by name."""

    name = ListFilter(field_name="name")
    search_by_name = CharFilter(
        field_name="name", lookup_expr="icontains", distinct=True
    )
    search_credentials_by_name = CharFilter(
        field_name="credentials__name", lookup_expr="icontains", distinct=True
    )

    class Meta:
        """Metadata for filterset."""

        model = Source
        fields = ["name", "source_type", "search_by_name", "search_credentials_by_name"]


class SourceViewSet(ModelViewSet):
    """A view set for Sources."""

    queryset = Source.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SourceFilter
    ordering_fields = ("name", "source_type", "most_recent_connect_scan__start_time")
    ordering = ("name",)

    def get_serializer_class(self):
        """Return the Serializer Class for this request."""
        if self.request.version == "v1":
            return SourceSerializerV1
        else:
            return SourceSerializerV2

    def list(self, request):
        """List the sources."""
        # List objects
        result = []
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for source in serializer.data:
                # Create expanded host cred JSON
                format_source(source)
                result.append(source)
            return self.get_paginated_response(serializer.data)

        for source in queryset:
            serializer = self.get_serializer(source)
            json_source = serializer.data

            # Create expanded host cred JSON
            format_source(json_source)

            result.append(json_source)
        return Response(result)

    def create(self, request, *args, **kwargs):
        """Create a source."""
        with transaction.atomic():
            response = super().create(request, args, kwargs)
            # format source after creating scan to populate connection
            format_source(response.data)
        return response

    def retrieve(self, request, pk=None):
        """Get a source."""
        if not pk or (pk and not is_int(pk)):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)

        source = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(source)
        json_source = serializer.data

        # Create expanded host cred JSON
        format_source(json_source)

        return Response(json_source)

    def update(self, request, *args, **kwargs):
        """Update a source."""
        # Note: This method's implementation is basically a straight copy of
        # rest_framework.mixins.UpdateModelMixin but modified to include the
        # call to format_source. We should probably refactor things here
        # to reduce duplication of code.
        source = self.get_object()
        serializer = self.get_serializer(
            source, data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        json_source = serializer.data

        # Create expanded host cred JSON
        format_source(json_source)

        return Response(json_source)

    @transaction.atomic
    def destroy(self, request, pk):
        """Delete a source."""
        try:
            source = Source.objects.get(pk=pk)
            scans = Scan.objects.filter(sources__pk=pk).values(IDENTIFIER_KEY, NAME_KEY)
            if scans:
                message = messages.SOURCE_DELETE_NOT_VALID_W_SCANS
                error = {"detail": message}
                slim_scans = []
                for scan in scans:
                    slim_scans.append(scan)
                error["scans"] = slim_scans
                raise ValidationError(error)
            source.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Source.DoesNotExist as exception:
            raise Http404 from exception

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """Bulk delete sources."""
        ids = set_of_ids_or_all_str(request.data.get("ids"))

        with transaction.atomic():
            sources = Source.objects.all()
            if ids != ALL_IDS_MAGIC_STRING:
                sources = sources.filter(id__in=ids)
            source_ids_requested = ids if isinstance(ids, set) else set()
            source_ids_found = set(sources.values_list("id", flat=True))
            source_ids_with_scans = (
                sources.exclude(scan=None)
                .prefetch_related("scan")
                .values_list("id", "scan")
                .order_by("id")
            )
            sources.filter(scan=None).delete()

        source_ids_missing = source_ids_requested - source_ids_found

        source_ids_skipped = []
        for source_id, grouper in groupby(source_ids_with_scans, key=lambda c: c[0]):
            source_ids_skipped.append(
                {"source": source_id, "scans": [g[1] for g in grouper]}
            )

        source_ids_deleted = source_ids_found - set(
            c["source"] for c in source_ids_skipped
        )

        message = _(
            "Deleted {count_deleted} sources. "
            "Could not find {count_missing} sources. "
            "Failed to delete {count_failed} sources."
        ).format(
            count_deleted=len(source_ids_deleted),
            count_missing=len(source_ids_missing),
            count_failed=len(source_ids_skipped),
        )

        response_data = {
            "message": message,
            "deleted": source_ids_deleted,
            "missing": source_ids_missing,
            "skipped": source_ids_skipped,
        }

        return Response(data=response_data, status=status.HTTP_200_OK)
