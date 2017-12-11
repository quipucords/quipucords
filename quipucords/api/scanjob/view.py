#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Describes the views associated with the API models."""

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
import api.messages as messages
from api.models import ScanJob, ConnectionResults, InspectionResults
from api.serializers import (ScanJobSerializer,
                             SourceSerializer,
                             ConnectionResultsSerializer,
                             SystemConnectionResultSerializer,
                             InspectionResultsSerializer,
                             SystemInspectionResultSerializer,
                             RawFactSerializer)
from api.signals.scanjob_signal import (start_scan, pause_scan,
                                        cancel_scan, restart_scan)


SOURCE_KEY = 'source'
RESULTS_KEY = 'results'


def expand_source(scan, json_scan):
    """Expand the source.

    Take scan object with source id and pull object from db.
    create slim dictionary version of source with name an value
    to return to user.
    """
    if json_scan[SOURCE_KEY]:
        source = scan.source
        slim_source = {'id': source.id, 'name': source.name,
                       'source_type': source.source_type}
        json_scan[SOURCE_KEY] = slim_source


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
        for result in job_conn_result.results.all():
            source_serializer = SourceSerializer(result.source)
            json_source = source_serializer.data
            json_source.pop('credentials', None)
            json_source.pop('hosts', None)
            json_source.pop('ssh_port', None)
            json_source.pop('address', None)
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
        for result in job_inspect_result.results.all():
            source_serializer = SourceSerializer(result.source)
            json_source = source_serializer.data
            json_source.pop('credentials', None)
            json_source.pop('hosts', None)
            json_source.pop('ssh_port', None)
            json_source.pop('address', None)
            systems = expand_sys_inspect_results(result)
            json_job_inspect_result_out = {'source': json_source,
                                           'systems': systems}
            json_job_inspect_result_list.append(json_job_inspect_result_out)
        json_job_inspect_result[RESULTS_KEY] = json_job_inspect_result_list


# pylint: disable=too-many-ancestors
class ScanJobViewSet(mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """A view set for ScanJob."""

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a scanjob."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        scanjob_obj = ScanJob.objects.get(pk=serializer.data['id'])
        fact_endpoint = request.build_absolute_uri(reverse('facts-list'))
        start_scan.send(sender=self.__class__, instance=scanjob_obj,
                        fact_endpoint=fact_endpoint)

        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request):  # pylint: disable=unused-argument
        """List the collection of scan jobs."""
        queryset = self.filter_queryset(self.get_queryset())
        result = []
        for scan in queryset:
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_source(scan, json_scan)
            result.append(json_scan)
        return Response(result)

    # pylint: disable=unused-argument, arguments-differ
    def retrieve(self, request, pk=None):
        """Get a scan job."""
        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanJobSerializer(scan)
        json_scan = serializer.data
        expand_source(scan, json_scan)
        return Response(json_scan)

    # pylint: disable=unused-argument,invalid-name,no-self-use
    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        """Get the results of a scan job."""
        result = None
        job_conn_result = ConnectionResults.objects.all() \
            .filter(scan_job__id=pk).first()
        job_scan_result = InspectionResults.objects.all() \
            .filter(scan_job__id=pk).first()
        if job_conn_result:
            serializer = ConnectionResultsSerializer(job_conn_result)
            json_job_conn_result = serializer.data
            expand_conn_results(job_conn_result, json_job_conn_result)
            if result is None:
                result = {}
            result['connection_results'] = json_job_conn_result
        if job_scan_result:
            serializer = InspectionResultsSerializer(job_scan_result)
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
        scan = get_object_or_404(self.queryset, pk=pk)
        if scan.status == ScanJob.RUNNING:
            pause_scan.send(sender=self.__class__, instance=scan)
            scan.status = ScanJob.PAUSED
            scan.save()
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_source(scan, json_scan)
            return Response(json_scan, status=200)
        elif scan.status == ScanJob.PAUSED:
            err_msg = _(messages.ALREADY_PAUSED)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        err_msg = _(messages.NO_PAUSE)
        return JsonResponse({'non_field_errors': [err_msg]}, status=400)

    @detail_route(methods=['put'])
    def cancel(self, request, pk=None):
        """Cancel the running scan."""
        scan = get_object_or_404(self.queryset, pk=pk)
        if (scan.status == ScanJob.COMPLETED or
                scan.status == ScanJob.FAILED or
                scan.status == ScanJob.CANCELED):
            err_msg = _(messages.NO_CANCEL)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        cancel_scan.send(sender=self.__class__, instance=scan)
        scan.status = ScanJob.CANCELED
        scan.save()
        serializer = ScanJobSerializer(scan)
        json_scan = serializer.data
        expand_source(scan, json_scan)
        return Response(json_scan, status=200)

    @detail_route(methods=['put'])
    def restart(self, request, pk=None):
        """Restart a paused scan."""
        scan = get_object_or_404(self.queryset, pk=pk)
        if scan.status == ScanJob.PAUSED:
            fact_endpoint = request.build_absolute_uri(reverse('facts-list'))
            restart_scan.send(sender=self.__class__,
                              instance=scan,
                              fact_endpoint=fact_endpoint)
            scan.status = ScanJob.RUNNING
            scan.save()
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_source(scan, json_scan)
            return Response(json_scan, status=200)
        elif scan.status == ScanJob.RUNNING:
            err_msg = _(messages.ALREADY_RUNNING)
            return JsonResponse({'non_field_errors': [err_msg]}, status=400)

        err_msg = _(messages.NO_RESTART)
        return JsonResponse({'non_field_errors': [err_msg]}, status=400)
