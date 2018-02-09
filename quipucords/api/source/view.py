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
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import (TokenAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from api.filters import ListFilter
from api.serializers import SourceSerializer
from api.models import Source, Credential
import api.messages as messages
from api.common.util import is_int


CREDENTIALS_KEY = 'credentials'


def expand_credential(json_source):
    """Expand host credentials.

    Take source object with credential id and pull object from db.
    create slim dictionary version of the host credential with name an value
    to return to user.
    """
    cred_ids = json_source.get('credentials', [])
    slim_cred = Credential.objects.filter(pk__in=cred_ids).values('id', 'name')
    # Update source JSON with cred JSON
    if slim_cred:
        json_source[CREDENTIALS_KEY] = slim_cred


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
        authentication_classes = (TokenAuthentication, SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = SourceFilter
    ordering_fields = ('name', 'source_type')
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
                expand_credential(source)
                result.append(source)
            return self.get_paginated_response(serializer.data)

        for source in queryset:
            serializer = SourceSerializer(source)
            json_source = serializer.data

            # Create expanded host cred JSON
            expand_credential(json_source)

            result.append(json_source)
        return Response(result)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a source."""
        response = super().create(request, args, kwargs)

        # Modify json for response
        json_source = response.data
        source_id = json_source.get('id')
        if not source_id or (source_id and not isinstance(source_id, int)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        get_object_or_404(self.queryset, pk=source_id)

        # Create expanded host cred JSON
        expand_credential(json_source)
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
        expand_credential(json_source)

        return Response(json_source)

    # pylint: disable=unused-argument
    def update(self, request, *args, **kwargs):
        """Update a source."""
        # Note: This method's implementation is basically a straight copy of
        # rest_framework.mixins.UpdateModelMixin but modified to include the
        # call to expand_credential. We should probably refactor things here
        # to reduce duplication of code.
        source = self.get_object()
        serializer = self.get_serializer(source, data=request.data,
                                         partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        json_source = serializer.data

        # Create expanded host cred JSON
        expand_credential(json_source)

        return Response(json_source)
