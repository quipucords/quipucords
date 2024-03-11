"""Describes the views associated with the API models."""


from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import (
    convert_to_boolean,
    expand_scanjob_with_times,
    is_boolean,
    is_int,
)
from api.filters import ListFilter
from api.models import Scan, ScanJob, ScanTask, Source
from api.serializers import SourceSerializerV1, SourceSerializerV2
from api.signal.scanjob_signal import start_scan
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

        json_scan_job = expand_scanjob_with_times(scan_job, connect_only=True)
        source_id = json_source.get("id")
        task_for_source = scan_job.tasks.filter(source=source_id).first()

        if task_for_source is not None:
            json_scan_job["source_systems_count"] = task_for_source.systems_count
            json_scan_job["source_systems_scanned"] = task_for_source.systems_scanned
            json_scan_job["source_systems_failed"] = task_for_source.systems_failed
            json_scan_job[
                "source_systems_unreachable"
            ] = task_for_source.systems_unreachable

        json_source["connection"] = json_scan_job
    return json_source


class SourceFilter(FilterSet):
    """Filter for sources by name."""

    name = ListFilter(field_name="name")
    search_by_name = CharFilter(
        field_name="name", lookup_expr="contains", distinct=True
    )
    search_credentials_by_name = CharFilter(
        field_name="credentials__name", lookup_expr="contains", distinct=True
    )

    class Meta:
        """Metadata for filterset."""

        model = Source
        fields = ["name", "source_type", "search_by_name", "search_credentials_by_name"]


class SourceViewSet(ModelViewSet):
    """A view set for Sources."""

    permission_classes = (IsAuthenticated,)

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
        # check to see if a connection scan was requested
        # through query parameter
        scan = request.query_params.get("scan", False)
        scan_job = None
        with transaction.atomic():
            response = super().create(request, args, kwargs)

            # Modify json for response
            if not is_boolean(scan):
                error = {"scan": [_(messages.SOURCE_CONNECTION_SCAN)]}
                raise ValidationError(error)

            # If the scan was requested, create a connection scan
            if convert_to_boolean(scan):
                # Grab the source id
                source_id = response.data["id"]

                # Create the scan job
                scan_job = ScanJob.objects.create(scan_type=ScanTask.SCAN_TYPE_CONNECT)

                # Add the source
                scan_job.sources.add(source_id)
                response.data["most_recent_connect_scan"] = scan_job.id

            # format source after creating scan to populate connection
            format_source(response.data)
        if scan_job:
            # start the scan outside of the transaction to avoid celery trying to start
            # the process with an id that doesn't exist in the DB yet.
            start_scan.send(sender=self.__class__, instance=scan_job)
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
        """Delete a cred."""
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
