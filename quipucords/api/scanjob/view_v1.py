"""Describes the views associated with the API models."""

import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.pagination import StandardResultsSetPagination
from api.common.util import is_int
from api.inspectresult.model import InspectResult
from api.models import Credential, ScanJob, ScanTask, Source
from api.scanjob.serializer import expand_scanjob
from api.serializers import (
    ScanJobSerializerV1,
    SystemConnectionResultSerializer,
    SystemInspectionResultSerializer,
)
from api.signal.scanjob_signal import cancel_scan

logger = logging.getLogger(__name__)

RESULTS_KEY = "task_results"


def expand_source(system):
    """Expand the json source."""
    if "source" in system.keys():
        source_id = system["source"]
        if source_id is None:
            system["source"] = "deleted"
        else:
            system["source"] = (
                Source.objects.filter(id=source_id)
                .values("id", "name", "source_type")
                .first()
            )


def expand_system_connection(system):
    """Expand the system connection results.

    :param system: A dictionary for a conn system result.
    """
    expand_source(system)
    if "credential" in system.keys():
        cred_id = system["credential"]
        system["credential"] = (
            Credential.objects.filter(id=cred_id).values("id", "name").first()
        )


def expand_system_inspection(system):
    """Expand the system inspection results.

    :param system: A dictionary for a inspection system result.
    """
    expand_source(system)


class ScanJobFilter(FilterSet):
    """Filter for sources by name."""

    class Meta:
        """Metadata for filterset."""

        model = ScanJob
        fields = ["status", "scan_type"]


class ScanJobViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A view set for ScanJob."""

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializerV1
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ScanJobFilter
    ordering_fields = ("id", "scan_type", "status", "start_time", "end_time")
    ordering = ("id",)

    def retrieve(self, request, pk=None):
        """Get a scan job."""
        if not pk or (pk and not is_int(pk)):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)

        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanJobSerializerV1(scan)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)
        return Response(json_scan)

    @staticmethod
    def handle_result_filters(request):
        """Get the associated filter parameters or return validation errors.

        @param request: The incoming request
        @returns: A tuple of ordering filter, status filter,
            and source_id filter
        """
        valid_orderging_filters = ["name", "status", "-name", "-status"]
        valid_status_filters = ["success", "failed", "unreachable"]
        ordering_param = "ordering"
        default_ordering = "status"
        status_param = "status"
        source_id_param = "source_id"
        ordering_filter = request.query_params.get(ordering_param, default_ordering)
        status_filter = request.query_params.get(status_param, None)
        source_id_filter = request.query_params.get(source_id_param, None)

        # validate query params
        if ordering_filter and ordering_filter not in valid_orderging_filters:
            valid_list = ", ".join(valid_orderging_filters)
            message = _(messages.QUERY_PARAM_INVALID % (ordering_param, valid_list))
            error = {"detail": [message]}
            raise ValidationError(error)
        if status_filter and status_filter not in valid_status_filters:
            valid_list = ", ".join(valid_status_filters)
            message = _(messages.QUERY_PARAM_INVALID % (status_param, valid_list))
            error = {"detail": [message]}
            raise ValidationError(error)
        if source_id_filter and not is_int(source_id_filter):
            message = _(
                messages.QUERY_PARAM_INVALID % (source_id_param, "source identifiers")
            )
            error = {"detail": [message]}
            raise ValidationError(error)

        return (ordering_filter, status_filter, source_id_filter)

    @action(detail=True, methods=["get"])
    def connection(self, request, pk=None):
        """Get the connection results of a scan job."""
        ordering_filter, status_filter, source_id_filter = self.handle_result_filters(
            request
        )

        try:
            scan_job = get_object_or_404(self.queryset, pk=pk)
            all_tasks = scan_job.connection_results.task_results.all()
        except ValueError:
            return Response(status=400)

        system_result_queryset = None
        for task_result in all_tasks:
            if system_result_queryset is None:
                system_result_queryset = task_result.systems.all()
            else:
                system_result_queryset = (
                    system_result_queryset | task_result.systems.all()
                )
        # create ordered queryset and assign the paginator
        ordered_query_set = system_result_queryset.order_by(ordering_filter)
        if status_filter:
            ordered_query_set = ordered_query_set.filter(status=status_filter)
        if source_id_filter:
            ordered_query_set = ordered_query_set.filter(source__id=source_id_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(ordered_query_set, request)

        if page is not None:
            serializer = SystemConnectionResultSerializer(page, many=True)
            for system in serializer.data:
                expand_system_connection(system)
            return paginator.get_paginated_response(serializer.data)
        return Response(status=404)

    @action(detail=True, methods=["get"])
    def inspection(self, request, pk=None):
        """Get the inspection results of a scan job."""
        ordering_filter, status_filter, source_id_filter = self.handle_result_filters(
            request
        )

        try:
            scan_job = get_object_or_404(self.queryset, pk=pk)
        except ValueError:
            return Response(status=400)
        system_result_queryset = InspectResult.objects.filter(
            inspect_group__tasks__job=scan_job
        )
        # create ordered queryset and assign the paginator
        paginator = StandardResultsSetPagination()
        ordered_query_set = system_result_queryset.order_by(ordering_filter)
        if status_filter:
            ordered_query_set = ordered_query_set.filter(status=status_filter)
        if source_id_filter:
            ordered_query_set = ordered_query_set.filter(
                inspect_group__source__id=source_id_filter
            )

        page = paginator.paginate_queryset(ordered_query_set, request)

        if page is not None:
            serializer = SystemInspectionResultSerializer(page, many=True)
            for system in serializer.data:
                expand_system_inspection(system)
            return paginator.get_paginated_response(serializer.data)
        return Response(status=404)

    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        """Cancel the running scan."""
        if not pk or (pk and not is_int(pk)):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
        scan = get_object_or_404(self.queryset, pk=pk)
        if scan.status in (ScanTask.COMPLETED, ScanTask.FAILED, ScanTask.CANCELED):
            err_msg = _(messages.NO_CANCEL)
            return JsonResponse({"non_field_errors": [err_msg]}, status=400)

        # Kill job before changing job state
        cancel_scan.send(sender=self.__class__, instance=scan)
        scan.status_cancel()
        serializer = ScanJobSerializerV1(scan)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)
        return Response(json_scan, status=200)
