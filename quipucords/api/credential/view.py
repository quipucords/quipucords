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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from django_filters.rest_framework import (DjangoFilterBackend,
                                           FilterSet)
from filters import mixins
from api.filters import ListFilter
from api.serializers import CredentialSerializer
from api.models import Credential, Source
import api.messages as messages
from api.common.util import is_int

IDENTIFIER_KEY = 'id'
NAME_KEY = 'name'
SOURCES_KEY = 'sources'
PASSWORD_KEY = 'password'
BECOME_PASSWORD_KEY = 'become_password'
SSH_PASSPHRASE_KEY = 'ssh_passphrase'
PASSWORD_MASK = '********'


def mask_credential(cred):
    """Masks the sensitive values in a credential from being returned on read.

    :param cred: a dictionary of values that may be masked
    :returns: the masked dictionary if it contains sensitive data
    """
    if cred.get(PASSWORD_KEY):
        cred[PASSWORD_KEY] = PASSWORD_MASK
    if cred.get(BECOME_PASSWORD_KEY):
        cred[BECOME_PASSWORD_KEY] = PASSWORD_MASK
    if cred.get(SSH_PASSPHRASE_KEY):
        cred[SSH_PASSPHRASE_KEY] = PASSWORD_MASK
    return cred


def format_credential(cred):
    """Update the credential with sources information and mask sensitive data.

    :param cred: a dictionary of values that may be masked
    :returns: the masked dictionary if it contains sensitive data
    and added sources if present
    """
    identifier = cred.get(IDENTIFIER_KEY)
    if identifier:
        slim_sources = Source.objects.filter(
            credentials__pk=identifier).values(IDENTIFIER_KEY, NAME_KEY)
        if slim_sources:
            cred[SOURCES_KEY] = slim_sources

    return mask_credential(cred)


class CredentialFilter(FilterSet):
    """Filter for host credentials by name."""

    name = ListFilter(name='name')

    class Meta:
        """Metadata for filterset."""

        model = Credential
        fields = ['name', 'cred_type']


# pylint: disable=too-many-ancestors
class CredentialViewSet(mixins.FiltersMixin, ModelViewSet):
    """A view set for the Credential model."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = CredentialFilter
    ordering_fields = ('name', 'cred_type')
    ordering = ('name',)

    def list(self, request):  # pylint: disable=unused-argument
        """List the host credentials."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for cred in serializer.data:
                cred = format_credential(cred)
            return self.get_paginated_response(serializer.data)

        serializer = CredentialSerializer(queryset, many=True)
        for cred in serializer.data:
            cred = format_credential(cred)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a host credential."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        cred = format_credential(serializer.data)
        return Response(cred, status=status.HTTP_201_CREATED,
                        headers=headers)

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        """Get a host credential."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        host_cred = get_object_or_404(self.queryset, pk=pk)
        serializer = CredentialSerializer(host_cred)
        cred = format_credential(serializer.data)
        return Response(cred)

    # pylint: disable=unused-argument
    def update(self, request, *args, **kwargs):
        """Update a host credential."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        cred = format_credential(serializer.data)
        return Response(cred)

    def partial_update(self, request, *args, **kwargs):
        """Update (partially) a host credential."""
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        cred = format_credential(serializer.data)
        return Response(cred)
