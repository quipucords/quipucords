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

from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.shortcuts import get_object_or_404
from api.scanjob_model import ScanJob
from api.scanjob_serializer import ScanJobSerializer
from api.networkprofile_model import NetworkProfile
from api.scanresults_model import ScanJobResults, Results, ResultKeyValue
from api.scanresults_serializer import (ScanJobResultsSerializer,
                                        ResultsSerializer,
                                        ResultKeyValueSerializer)


PROFILE_KEY = 'profile'
ROW_KEY = 'row'
COLUMN_KEY = 'columns'
RESULTS_KEY = 'results'


def expand_network_profile(scan):
    """Take scan object with profile id and pull object from db.
    create slim dictionary version of profile with name an value
    to return to user.
    """
    if scan[PROFILE_KEY]:
        profile_id = scan[PROFILE_KEY]
        profile = NetworkProfile.objects.get(pk=profile_id)
        slim_profile = {'id': profile_id, 'name': profile.name}
        scan[PROFILE_KEY] = slim_profile
    return scan


def expand_key_values(result_columns):
    """Take collection of result key value ids and pull objects from db.
    create slim dictionary version of key/value to return to user.
    """
    if result_columns is not None and result_columns[COLUMN_KEY]:
        fields_list = []
        for field_id in result_columns[COLUMN_KEY]:
            field_data = ResultKeyValue.objects.get(pk=field_id)
            serializer = ResultKeyValueSerializer(field_data)
            print(serializer.data)
            field_out = {'key': serializer.data['key'],
                         'value': serializer.data['value']}
            fields_list.append(field_out)
    return fields_list


def expand_scan_results(results):
    """Take collection of results ids and pull objects from db.
    create slim dictionary version of rows of key/value to return to user.
    """
    if results is not None and results[RESULTS_KEY]:
        results_list = []
        for results_id in results[RESULTS_KEY]:
            results_data = Results.objects.get(pk=results_id)
            serializer = ResultsSerializer(results_data)
            columns_out = expand_key_values(serializer.data)
            results_out = {ROW_KEY: serializer.data[ROW_KEY],
                           COLUMN_KEY: columns_out}
            results_list.append(results_out)
        results[RESULTS_KEY] = results_list
    return results


# pylint: disable=too-many-ancestors
class ScanJobViewSet(mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """A view set for ScanJob"""

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer

    def list(self, request):  # pylint: disable=unused-argument
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ScanJobSerializer(queryset, many=True)
        for scan in serializer.data:
            scan = expand_network_profile(scan)
        return Response(serializer.data)

    # pylint: disable=unused-argument, arguments-differ
    def retrieve(self, request, pk=None):
        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanJobSerializer(scan)
        scan_out = expand_network_profile(serializer.data)
        return Response(scan_out)

    # pylint: disable=unused-argument,invalid-name
    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        """Get the results of a scan job"""
        get_object_or_404(self.queryset, pk=pk)
        results_queryset = ScanJobResults.objects.all()
        results = get_object_or_404(results_queryset, scan_job=pk)
        serializer = ScanJobResultsSerializer(results)
        results_out = expand_scan_results(serializer.data)
        return Response(results_out)
