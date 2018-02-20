#
# Copyright (c) 2018 Red Hat, Inc.
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
from rest_framework.decorators import detail_route
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
import api.messages as messages
from api.common.util import is_int
from api.models import (Scan, ScanJob, Source)
from api.serializers import (ScanSerializer, ScanJobSerializer)
from api.scanjob.serializer import expand_scanjob
from api.signals.scanjob_signal import start_scan


# pylint: disable=too-many-branches

SOURCES_KEY = 'sources'


def expand_scan(json_scan):
    """Expand the scan object's sources."""
    source_ids = json_scan.get(SOURCES_KEY, [])
    slim_sources = Source.objects.filter(
        pk__in=source_ids).values('id', 'name', 'source_type')
    if slim_sources:
        json_scan[SOURCES_KEY] = slim_sources


class ScanFilter(FilterSet):
    """Filter for sources by name."""

    class Meta:
        """Metadata for filterset."""

        model = Scan
        fields = ['scan_type']


# pylint: disable=too-many-ancestors
class ScanViewSet(ModelViewSet):
    """A view set for Scan."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = ScanFilter
    ordering_fields = ('id', 'name', 'scan_type')
    ordering = ('name',)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a scan."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request):  # pylint: disable=unused-argument
        """List the collection of scan."""
        result = []
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for scan in serializer.data:
                expand_scan(scan)
                result.append(scan)
            return self.get_paginated_response(serializer.data)

        for scan in queryset:
            serializer = ScanSerializer(scan)
            json_scan = serializer.data
            expand_scan(json_scan)
            result.append(json_scan)
        return Response(result)

    # pylint: disable=unused-argument, arguments-differ
    def retrieve(self, request, pk=None):
        """Get a scan."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanSerializer(scan)
        json_scan = serializer.data
        expand_scan(json_scan)
        return Response(json_scan)

    @detail_route(methods=['get', 'post'])
    def jobs(self, request, pk=None):
        """Get the jobs of a scan."""
        result = []
        scan = get_object_or_404(self.queryset, pk=pk)
        if request.method == 'GET':
            jobs = ScanJob.objects.filter(scan=scan)
            page = self.paginate_queryset(jobs)

            if page is not None:
                serializer = ScanJobSerializer(page, many=True)
                for scan in serializer.data:
                    json_scan = expand_scanjob(scan)
                    result.append(json_scan)
                return self.get_paginated_response(serializer.data)

            for job in jobs:
                job_serializer = ScanJobSerializer(job)
                job_json = job_serializer.data
                job_json = expand_scanjob(job_serializer.data)
                result.append(job_json)
            return Response(result)
        else:
            job_data = request.data.copy()
            job_data['scan'] = pk
            job_serializer = ScanJobSerializer(data=job_data)
            job_serializer.is_valid(raise_exception=True)
            job_serializer.save()
            headers = self.get_success_headers(job_serializer.data)
            scanjob_obj = ScanJob.objects.get(pk=job_serializer.data['id'])
            scanjob_obj.log_current_status()
            start_scan.send(sender=self.__class__, instance=scanjob_obj)

            return Response(job_serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers)
