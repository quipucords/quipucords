#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Describes the views associated with the API models."""

import json
import logging
import os

import api.messages as messages
from api.common.pagination import StandardResultsSetPagination
from api.common.util import is_int
from api.models import (Credential,
                        RawFact,
                        ScanJob,
                        ScanTask,
                        Source)
from api.scanjob.serializer import expand_scanjob
from api.serializers import (ScanJobSerializer,
                             SystemConnectionResultSerializer,
                             SystemInspectionResultSerializer)
from api.signal.scanjob_signal import (cancel_scan,
                                       pause_scan,
                                       restart_scan)


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)

from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

RESULTS_KEY = 'task_results'


def expand_source(system):
    """Expand the json source."""
    if 'source' in system.keys():
        source_id = system['source']
        if source_id is None:
            system['source'] = 'deleted'
        else:
            system['source'] = \
                Source.objects.filter(
                    id=source_id).values('id',
                                         'name',
                                         'source_type').first()


def expand_system_connection(system):
    """Expand the system connection results.

    :param system: A dictionary for a conn system result.
    """
    expand_source(system)
    if 'credential' in system.keys():
        cred_id = system['credential']
        system['credential'] = \
            Credential.objects.filter(id=cred_id).values('id',
                                                         'name').first()


def expand_system_inspection(system):
    """Expand the system inspection results.

    :param system: A dictionary for a inspection system result.
    """
    expand_source(system)
    if 'facts' in system.keys():
        facts = []
        fact_ids = system['facts']
        for fact_id in fact_ids:
            raw_fact = RawFact.objects.filter(
                id=fact_id).values('name', 'value').first()
            if raw_fact.get('value') is not None:
                raw_fact['value'] = json.loads(raw_fact['value'])
            facts.append(raw_fact)
        system['facts'] = facts


class ScanJobFilter(FilterSet):
    """Filter for sources by name."""

    class Meta:
        """Metadata for filterset."""

        model = ScanJob
        fields = ['status', 'scan_type']


# pylint: disable=too-many-ancestors
class ScanJobViewSet(mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """A view set for ScanJob."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = ScanJobFilter
    ordering_fields = ('id', 'scan_type', 'status', 'start_time', 'end_time')
    ordering = ('id',)

    # pylint: disable=unused-argument, arguments-differ,invalid-name
    def retrieve(self, request, pk=None):
        """Get a scan job."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanJobSerializer(scan)
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
        valid_orderging_filters = ['name', 'status', '-name', '-status']
        valid_status_filters = ['success', 'failed', 'unreachable']
        ordering_param = 'ordering'
        default_ordering = 'status'
        status_param = 'status'
        source_id_param = 'source_id'
        ordering_filter = request.query_params.get(ordering_param,
                                                   default_ordering)
        status_filter = request.query_params.get(status_param, None)
        source_id_filter = request.query_params.get(source_id_param, None)

        # validate query params
        if ordering_filter and ordering_filter not in valid_orderging_filters:
            valid_list = ', '.join(valid_orderging_filters)
            message = _(messages.QUERY_PARAM_INVALID %
                        (ordering_param, valid_list))
            error = {
                'detail': [message]
            }
            raise ValidationError(error)
        if status_filter and status_filter not in valid_status_filters:
            valid_list = ', '.join(valid_status_filters)
            message = _(messages.QUERY_PARAM_INVALID %
                        (status_param, valid_list))
            error = {
                'detail': [message]
            }
            raise ValidationError(error)
        if source_id_filter and not is_int(source_id_filter):
            message = _(messages.QUERY_PARAM_INVALID %
                        (source_id_param, 'source identifiers'))
            error = {
                'detail': [message]
            }
            raise ValidationError(error)

        return (ordering_filter, status_filter, source_id_filter)

    @detail_route(methods=['get'])
    def connection(self, request, pk=None):
        """Get the connection results of a scan job."""
        ordering_filter, status_filter, source_id_filter = \
            self.handle_result_filters(request)

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
                system_result_queryset = \
                    system_result_queryset | task_result.systems.all()
        # create ordered queryset and assign the paginator
        ordered_query_set = system_result_queryset.order_by(ordering_filter)
        if status_filter:
            ordered_query_set = ordered_query_set.filter(status=status_filter)
        if source_id_filter:
            ordered_query_set = \
                ordered_query_set.filter(source__id=source_id_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(ordered_query_set, request)

        if page is not None:
            serializer = SystemConnectionResultSerializer(page, many=True)
            for system in serializer.data:
                expand_system_connection(system)
            return paginator.get_paginated_response(serializer.data)
        return Response(status=404)

    @detail_route(methods=['get'])
    def inspection(self, request, pk=None):
        """Get the inspection results of a scan job."""
        ordering_filter, status_filter, source_id_filter = \
            self.handle_result_filters(request)

        try:
            scan_job = get_object_or_404(self.queryset, pk=pk)
            all_tasks = scan_job.inspection_results.task_results.all()
        except ValueError:
            return Response(status=400)
        system_result_queryset = None
        for task_result in all_tasks:
            if system_result_queryset is None:
                system_result_queryset = task_result.systems.all()
            else:
                system_result_queryset = \
                    system_result_queryset | task_result.systems.all()
        # create ordered queryset and assign the paginator
        paginator = StandardResultsSetPagination()
        ordered_query_set = system_result_queryset.order_by(ordering_filter)
        if status_filter:
            ordered_query_set = ordered_query_set.filter(status=status_filter)
        if source_id_filter:
            ordered_query_set = \
                ordered_query_set.filter(source__id=source_id_filter)

        page = paginator.paginate_queryset(ordered_query_set, request)

        if page is not None:
            serializer = SystemInspectionResultSerializer(page, many=True)
            for system in serializer.data:
                expand_system_inspection(system)
            return paginator.get_paginated_response(serializer.data)
        return Response(status=404)

    @detail_route(methods=['put'])
    def pause(self, request, pk=None):
        """Pause the running scan."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
        scan = get_object_or_404(self.queryset, pk=pk)
        if scan.status == ScanTask.RUNNING:
            # Kill job before changing job state
            pause_scan.send(sender=self.__class__, instance=scan)
            scan.pause()
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            json_scan = expand_scanjob(json_scan)
            return Response(json_scan, status=200)
        elif scan.status == ScanTask.PAUSED:
            err_msg = _(messages.ALREADY_PAUSED)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        err_msg = _(messages.NO_PAUSE)
        return JsonResponse({'non_field_errors': [err_msg]}, status=400)

    @detail_route(methods=['put'])
    def cancel(self, request, pk=None):
        """Cancel the running scan."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
        scan = get_object_or_404(self.queryset, pk=pk)
        if (scan.status == ScanTask.COMPLETED or
                scan.status == ScanTask.FAILED or
                scan.status == ScanTask.CANCELED):
            err_msg = _(messages.NO_CANCEL)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        # Kill job before changing job state
        cancel_scan.send(sender=self.__class__, instance=scan)
        scan.cancel()
        serializer = ScanJobSerializer(scan)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)
        return Response(json_scan, status=200)

    @detail_route(methods=['put'])
    def restart(self, request, pk=None):
        """Restart a paused scan."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
        scan = get_object_or_404(self.queryset, pk=pk)
        if scan.status == ScanTask.PAUSED:
            # Update job state before starting job
            scan.restart()
            restart_scan.send(sender=self.__class__,
                              instance=scan)
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            json_scan = expand_scanjob(json_scan)
            return Response(json_scan, status=200)
        elif scan.status == ScanTask.RUNNING:
            err_msg = _(messages.ALREADY_RUNNING)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        err_msg = _(messages.NO_RESTART)
        return JsonResponse({'non_field_errors': [err_msg]}, status=400)
