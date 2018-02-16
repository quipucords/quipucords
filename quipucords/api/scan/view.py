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
from api.models import (Scan, Source)
from api.serializers import (ScanSerializer)

SOURCES_KEY = 'sources'
RESULTS_KEY = 'task_results'
TASKS_KEY = 'tasks'
SYSTEMS_COUNT_KEY = 'systems_count'
SYSTEMS_SCANNED_KEY = 'systems_scanned'
SYSTEMS_FAILED_KEY = 'systems_failed'


# pylint: disable=too-many-branches
def expand_scan(json_scan):
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
    ordering_fields = ('id', 'scan_type', 'status', 'start_time', 'end_time')
    ordering = ('id',)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a scanjob."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
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
        """Get a scan job."""
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
