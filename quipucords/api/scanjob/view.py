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
from api.models import ScanJob, ScanJobResults
from api.serializers import (ScanJobSerializer,
                             ScanJobResultsSerializer,
                             ResultsSerializer,
                             ResultKeyValueSerializer)
from api.signals.scanjob_signal import (start_scan, pause_scan,
                                        cancel_scan, restart_scan)


SOURCE_KEY = 'source'
ROW_KEY = 'row'
COLUMN_KEY = 'columns'
RESULTS_KEY = 'results'


def expand_source(scan, json_scan):
    """Expand the source.

    Take scan object with source id and pull object from db.
    create slim dictionary version of source with name an value
    to return to user.
    """
    if json_scan[SOURCE_KEY]:
        source = scan.source
        slim_source = {'id': source.id, 'name': source.name}
        json_scan[SOURCE_KEY] = slim_source


def expand_key_values(result, json_result):
    """Expand the key values.

    Take collection of result key value ids and pull objects from db.
    create slim dictionary version of key/value to return to user.
    """
    columns = []
    if json_result is not None and json_result[COLUMN_KEY]:
        for column in result.columns.all():
            serializer = ResultKeyValueSerializer(column)
            json_column = serializer.data
            field_out = {'key': json_column['key'],
                         'value': json_column['value']}
            columns.append(field_out)
    return columns


def expand_scan_results(job_scan_result, json_job_scan_result):
    """Expand the scan results.

    Take collection of json_job_scan_result ids and pull objects from db.
    create slim dictionary version of rows of key/value to return to user.
    """
    if json_job_scan_result is not None and json_job_scan_result[RESULTS_KEY]:
        json_job_scan_result_list = []
        for result in job_scan_result.results.all():
            serializer = ResultsSerializer(result)
            json_result = serializer.data
            columns = expand_key_values(result, json_result)
            json_job_scan_result_out = {ROW_KEY: json_result[ROW_KEY],
                                        COLUMN_KEY: columns}
            json_job_scan_result_list.append(json_job_scan_result_out)
        json_job_scan_result[RESULTS_KEY] = json_job_scan_result_list


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
        job_scan_result = ScanJobResults.objects.all() \
            .filter(scan_job__id=pk).first()
        if job_scan_result:
            serializer = ScanJobResultsSerializer(job_scan_result)
            json_job_scan_result = serializer.data
            expand_scan_results(job_scan_result, json_job_scan_result)
            return Response(json_job_scan_result)
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
