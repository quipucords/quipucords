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

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from filters import mixins
from api.filters import ListFilter
from api.serializers import HostCredentialSerializer
from api.models import HostCredential

PASSWORD_KEY = 'password'
SUDO_PASSWORD_KEY = 'sudo_password'
SSH_PASSPHRASE_KEY = 'ssh_passphrase'
PASSWORD_MASK = '********'


def mask_credential(cred):
    """Masks the sensitive values in a credential from being returned on read.

    :param cred: a dictionary of values that may be masked
    :returns: the masked dictionary if it contains sensitive data
    """
    if cred[PASSWORD_KEY]:
        cred[PASSWORD_KEY] = PASSWORD_MASK
    if cred[SUDO_PASSWORD_KEY]:
        cred[SUDO_PASSWORD_KEY] = PASSWORD_MASK
    if cred[SSH_PASSPHRASE_KEY]:
        cred[SSH_PASSPHRASE_KEY] = PASSWORD_MASK
    return cred


class HostCredentialFilter(FilterSet):
    """Filter for host credentials by name."""

    name = ListFilter(name='name')

    class Meta:
        """Metadata for filterset."""

        model = HostCredential
        fields = ['name']


# pylint: disable=too-many-ancestors
class HostCredentialViewSet(mixins.FiltersMixin, ModelViewSet):
    """A view set for the HostCredential model."""

    queryset = HostCredential.objects.all()
    serializer_class = HostCredentialSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = HostCredentialFilter

    def list(self, request):  # pylint: disable=unused-argument
        """List the host credentials."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = HostCredentialSerializer(queryset, many=True)
        for cred in serializer.data:
            cred = mask_credential(cred)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a host credential."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        cred = mask_credential(serializer.data)
        return Response(cred, status=status.HTTP_201_CREATED,
                        headers=headers)

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        """Get a host credential."""
        host_cred = get_object_or_404(self.queryset, pk=pk)
        serializer = HostCredentialSerializer(host_cred)
        cred = mask_credential(serializer.data)
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
        cred = mask_credential(serializer.data)
        return Response(cred)
