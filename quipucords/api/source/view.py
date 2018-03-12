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
from django.http import Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from api.filters import ListFilter
from api.serializers import SourceSerializer
from api.models import (Source,
                        Scan,
                        ScanJob,
                        ScanTask)
import api.messages as messages
from api.common.util import is_int, is_boolean, convert_to_boolean, \
    expand_scanjob_with_times
from api.signals.scanjob_signal import start_scan
from api.source.util import expand_credential


IDENTIFIER_KEY = 'id'
NAME_KEY = 'name'


def format_source(json_source):
    """Format source with credentials and most recent connection scan.

    :param json_source: JSON source data from serializer
    :returns: JSON data
    """
    expand_credential(json_source)
    conn_job_id = json_source.pop('most_recent_connect_scan', None)
    if conn_job_id:
        scan_job = ScanJob.objects.get(pk=conn_job_id)
        json_scan_job = expand_scanjob_with_times(scan_job)
        json_source['connection'] = json_scan_job

    return json_source


class SourceFilter(FilterSet):
    """Filter for sources by name."""

    name = ListFilter(name='name')

    class Meta:
        """Metadata for filterset."""

        model = Source
        fields = ['name', 'source_type']


# pylint: disable=too-many-ancestors
class SourceViewSet(ModelViewSet):
    """A view set for Sources."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = SourceFilter
    ordering_fields = ('name', 'source_type',
                       'most_recent_connect_scan__start_time')
    ordering = ('name',)

    def list(self, request):  # pylint: disable=unused-argument
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
            serializer = SourceSerializer(source)
            json_source = serializer.data

            # Create expanded host cred JSON
            format_source(json_source)

            result.append(json_source)
        return Response(result)

    # pylint: disable=unused-argument
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a source."""
        response = super().create(request, args, kwargs)

        # Modify json for response
        json_source = response.data
        format_source(json_source)

        # check to see if a connection scan was requested
        # through query parameter
        scan = request.query_params.get('scan', False)
        # If the scan was requested, create a connection scan
        if scan:
            if is_boolean(scan):
                if convert_to_boolean(scan):
                    # Grab the source id
                    source_id = response.data['id']
                    # Create the scan job
                    scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
                    scan_job.save()

                    # Add the source
                    scan_job.sources.add(source_id)
                    scan_job.save()

                    # Start the scan
                    start_scan.send(sender=self.__class__, instance=scan_job)
            else:
                error = {
                    'scan': [_(messages.SOURCE_CONNECTION_SCAN)]
                }
                raise ValidationError(error)
        return response

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        """Get a source."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        source = get_object_or_404(self.queryset, pk=pk)
        serializer = SourceSerializer(source)
        json_source = serializer.data

        # Create expanded host cred JSON
        format_source(json_source)

        return Response(json_source)

    # pylint: disable=unused-argument
    def update(self, request, *args, **kwargs):
        """Update a source."""
        # Note: This method's implementation is basically a straight copy of
        # rest_framework.mixins.UpdateModelMixin but modified to include the
        # call to format_source. We should probably refactor things here
        # to reduce duplication of code.
        source = self.get_object()
        serializer = self.get_serializer(source, data=request.data,
                                         partial=kwargs.get('partial', False))
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
            scans = Scan.objects.filter(
                sources__pk=pk).values(IDENTIFIER_KEY, NAME_KEY)
            if scans:
                message = messages.SOURCE_DELETE_NOT_VALID_W_SCANS
                error = {'detail': message}
                slim_scans = []
                for scan in scans:
                    slim_scans.append(scan)
                error['scans'] = slim_scans
                raise ValidationError(error)
            source.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Source.DoesNotExist:
            raise Http404
