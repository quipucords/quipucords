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
"""Describes the views associated with the API models"""

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from api.models import ScanJob, NetworkProfile, ScanJobResults
from api.serializers import (ScanJobSerializer,
                             ScanJobResultsSerializer,
                             ResultsSerializer,
                             ResultKeyValueSerializer)
from scanner.discovery import DiscoveryScanner
from scanner.host import HostScanner


PROFILE_KEY = 'profile'
ROW_KEY = 'row'
COLUMN_KEY = 'columns'
RESULTS_KEY = 'results'


def expand_network_profile(scan, json_scan):
    """Take scan object with profile id and pull object from db.
    create slim dictionary version of profile with name an value
    to return to user.
    """
    if json_scan[PROFILE_KEY]:
        profile = scan.profile
        slim_profile = {'id': profile.id, 'name': profile.name}
        json_scan[PROFILE_KEY] = slim_profile


def expand_key_values(result, json_result):
    """Take collection of result key value ids and pull objects from db.
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
    """Take collection of json_job_scan_result ids and pull objects from db.
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
    """A view set for ScanJob"""

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        scanjob = serializer.data
        scan_type = scanjob['scan_type']
        scanjob_id = scanjob['id']
        scanjob_profile_id = scanjob['profile']
        scanjob_obj = ScanJob.objects.get(pk=scanjob_id)
        profile = NetworkProfile.objects.get(pk=scanjob_profile_id)
        if scan_type == ScanJob.DISCOVERY:
            scan = DiscoveryScanner(scanjob_obj, profile)
            scan.start()
        else:
            fact_endpoint = request.build_absolute_uri(reverse('facts-list'))
            scan = HostScanner(scanjob_obj, profile, fact_endpoint)
            scan.start()

        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request):  # pylint: disable=unused-argument
        queryset = self.filter_queryset(self.get_queryset())
        result = []
        for scan in queryset:
            serializer = ScanJobSerializer(scan)
            json_scan = serializer.data
            expand_network_profile(scan, json_scan)
            result.append(json_scan)
        return Response(result)

    # pylint: disable=unused-argument, arguments-differ
    def retrieve(self, request, pk=None):
        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanJobSerializer(scan)
        json_scan = serializer.data
        expand_network_profile(scan, json_scan)
        return Response(json_scan)

    # pylint: disable=unused-argument,invalid-name,no-self-use
    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        """Get the results of a scan job"""
        job_scan_result = ScanJobResults.objects.all() \
            .filter(scan_job__id=pk).first()
        if job_scan_result:
            serializer = ScanJobResultsSerializer(job_scan_result)
            json_job_scan_result = serializer.data
            expand_scan_results(job_scan_result, json_job_scan_result)
            return Response(json_job_scan_result)
        return Response(status=404)
