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

import os
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
import api.messages as messages
from api.common.util import is_int
from api.models import (ScanTask, ScanJob, Source)
from api.serializers import (ScanJobSerializer,
                             SourceSerializer,
                             JobConnectionResultSerializer,
                             SystemConnectionResultSerializer,
                             JobInspectionResultSerializer,
                             SystemInspectionResultSerializer,
                             RawFactSerializer)
from api.signals.scanjob_signal import (start_scan, pause_scan,
                                        cancel_scan, restart_scan)


SOURCES_KEY = 'sources'
RESULTS_KEY = 'task_results'
TASKS_KEY = 'tasks'
SYSTEMS_COUNT_KEY = 'systems_count'
SYSTEMS_SCANNED_KEY = 'systems_scanned'
SYSTEMS_FAILED_KEY = 'systems_failed'


# pylint: disable=too-many-branches
def expand_scanjob(json_scan):
    """Expand the source and calculate values.

    Take scan object with source ids and pull objects from db.
    create slim dictionary version of sources with name an value
    to return to user. Calculate systems_count, systems_scanned,
    systems_failed values from tasks.
    """
    source_ids = json_scan.get(SOURCES_KEY, [])
    slim_sources = Source.objects.filter(
        pk__in=source_ids).values('id', 'name', 'source_type')
    if slim_sources:
        json_scan[SOURCES_KEY] = slim_sources

    if json_scan.get(TASKS_KEY):
        scan = ScanJob.objects.get(pk=json_scan.get('id'))
        systems_count = None
        systems_scanned = None
        systems_failed = None
        tasks = scan.tasks.filter(
            scan_type=scan.scan_type).order_by('sequence_number')
        for task in tasks:
            if task.systems_count is not None:
                if systems_count is None:
                    systems_count = 0
                systems_count += task.systems_count
            if task.systems_scanned is not None:
                if systems_scanned is None:
                    systems_scanned = 0
                systems_scanned += task.systems_scanned
            if task.systems_failed is not None:
                if systems_failed is None:
                    systems_failed = 0
                systems_failed += task.systems_failed
        if systems_count is not None:
            json_scan[SYSTEMS_COUNT_KEY] = systems_count
        if systems_scanned is not None:
            json_scan[SYSTEMS_SCANNED_KEY] = systems_scanned
        if systems_failed is not None:
            json_scan[SYSTEMS_FAILED_KEY] = systems_failed


def expand_sys_conn_result(conn_result):
    """Expand the system connection results.

    Take collection of system connection result ids and pull objects from db.
    Return the user a json representation of these values.
    """
    result = []
    for system_result in conn_result.systems.all():
        serializer = SystemConnectionResultSerializer(system_result)
        json_sys_result = serializer.data
        if system_result.credential is not None:
            cred = system_result.credential
            json_cred = {'id': cred.id, 'name': cred.name}
            json_sys_result['credential'] = json_cred
        result.append(json_sys_result)
    return result


def expand_sys_inspect_results(inspect_result):
    """Expand the system inspection results.

    Take collection of system inspection result ids and pull objects from db.
    Return the user a json representation of these values.
    """
    result = []
    for system_result in inspect_result.systems.all():
        serializer = SystemInspectionResultSerializer(system_result)
        json_sys_result = serializer.data
        if system_result.facts is not None:
            facts = system_result.facts.all()
            json_facts = []
            for fact in facts:
                fact_serializer = RawFactSerializer(fact)
                json_fact = fact_serializer.data
                json_facts.append(json_fact)
            json_sys_result['facts'] = json_facts
        result.append(json_sys_result)
    return result


def expand_conn_results(job_conn_result, json_job_conn_result):
    """Expand the connection results.

    Take collection of json_job_conn_result ids and pull objects from db.
    create slim dictionary version of rows of key/value to return to user.
    """
    if json_job_conn_result is not None and\
            json_job_conn_result.get(RESULTS_KEY):
        json_job_conn_result_list = []
        for result in job_conn_result.task_results.all():
            conn_task = ScanTask.objects.filter(
                connection_result=result).first()
            source_serializer = SourceSerializer(conn_task.source)
            json_source = source_serializer.data
            json_source.pop('credentials', None)
            json_source.pop('hosts', None)
            json_source.pop('port', None)
            systems = expand_sys_conn_result(result)
            json_job_conn_result_out = {'source': json_source,
                                        'systems': systems}
            json_job_conn_result_list.append(json_job_conn_result_out)
        json_job_conn_result[RESULTS_KEY] = json_job_conn_result_list


def expand_inspect_results(job_inspect_result, json_job_inspect_result):
    """Expand the inspection results.

    Take collection of json_job_inspect_result ids and pull objects from db.
    create slim dictionary version of rows of key/value to return to user.
    """
    if json_job_inspect_result is not None and\
            json_job_inspect_result.get(RESULTS_KEY):
        json_job_inspect_result_list = []
        for result in job_inspect_result.task_results.all():
            inspect_task = ScanTask.objects.filter(
                inspection_result=result).first()
            source_serializer = SourceSerializer(inspect_task.source)
            json_source = source_serializer.data
            json_source.pop('credentials', None)
            json_source.pop('hosts', None)
            json_source.pop('port', None)
            systems = expand_sys_inspect_results(result)
            json_job_inspect_result_out = {'source': json_source,
                                           'systems': systems}
            json_job_inspect_result_list.append(json_job_inspect_result_out)
        json_job_inspect_result[RESULTS_KEY] = json_job_inspect_result_list


class ScanJobFilter(FilterSet):
    """Filter for sources by name."""

    class Meta:
        """Metadata for filterset."""

        model = ScanJob
        fields = ['status', 'scan_type']


# pylint: disable=too-many-ancestors
class ScanJobViewSet(mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.ListModelMixin,
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

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a scanjob."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        scanjob_obj = ScanJob.objects.get(pk=serializer.data['id'])
        scanjob_obj.log_current_status()
        start_scan.send(sender=self.__class__, instance=scanjob_obj)

        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request):  # pylint: disable=unused-argument
        """List the collection of scan jobs."""
        result = []
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for scan in serializer.data:
                expand_scanjob(scan)
                result.append(scan)
            return self.get_paginated_response(serializer.data)

        for scan in queryset:
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_scanjob(json_scan)
            result.append(json_scan)
        return Response(result)

    # pylint: disable=unused-argument, arguments-differ
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
        expand_scanjob(json_scan)
        return Response(json_scan)

    # pylint: disable=unused-argument,invalid-name,no-self-use
    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        """Get the results of a scan job."""
        result = None
        scan_job = get_object_or_404(self.queryset, pk=pk)
        job_conn_result = scan_job.connection_results
        job_scan_result = scan_job.inspection_results
        if job_conn_result:
            serializer = JobConnectionResultSerializer(job_conn_result)
            json_job_conn_result = serializer.data
            expand_conn_results(job_conn_result, json_job_conn_result)
            if result is None:
                result = {}
            result['connection_results'] = json_job_conn_result
        if job_scan_result:
            serializer = JobInspectionResultSerializer(job_scan_result)
            json_job_scan_result = serializer.data
            expand_inspect_results(job_scan_result, json_job_scan_result)
            if result is None:
                result = {}
            result['inspection_results'] = json_job_scan_result
        if result is not None:
            return Response(result)
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
            scan.pause()
            pause_scan.send(sender=self.__class__, instance=scan)
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_scanjob(json_scan)
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

        scan.cancel()
        cancel_scan.send(sender=self.__class__, instance=scan)
        serializer = ScanJobSerializer(scan)
        json_scan = serializer.data
        expand_scanjob(json_scan)
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
            scan.restart()
            restart_scan.send(sender=self.__class__,
                              instance=scan)
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_scanjob(json_scan)
            return Response(json_scan, status=200)
        elif scan.status == ScanTask.RUNNING:
            err_msg = _(messages.ALREADY_RUNNING)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        err_msg = _(messages.NO_RESTART)
        return JsonResponse({'non_field_errors': [err_msg]}, status=400)
