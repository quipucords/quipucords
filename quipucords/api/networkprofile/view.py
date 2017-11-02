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
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from api.filters import ListFilter
from api.serializers import NetworkProfileSerializer
from api.models import NetworkProfile


CREDENTIALS_KEY = 'credentials'


def expand_host_credential(profile, json_profile):
    """Expand host credentials.

    Take network profile object with credential id and pull object from db.
    create slim dictionary version of the host credential with name an value
    to return to user.
    """
    json_creds = None
    if profile.credentials:
        credentials = profile.credentials
        json_creds = []

        # For each cred, add subset fields to response
        for cred in credentials.all():
            slim_cred = {'id': cred.id, 'name': cred.name}
            json_creds.append(slim_cred)

    # Update profile JSON with cred JSON
    if json_creds:
        json_profile[CREDENTIALS_KEY] = json_creds


class NetworkProfileFilter(FilterSet):
    """Filter for network profiles by name."""

    name = ListFilter(name='name')

    class Meta:
        """Metadata for filterset."""

        model = NetworkProfile
        fields = ['name']


# pylint: disable=too-many-ancestors
class NetworkProfileViewSet(ModelViewSet):
    """A view set for NetworkProfiles."""

    queryset = NetworkProfile.objects.all()
    serializer_class = NetworkProfileSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = NetworkProfileFilter

    def list(self, request):  # pylint: disable=unused-argument
        """List the network profiles."""
        # List objects
        queryset = self.filter_queryset(self.get_queryset())

        # For each profile, expand creds
        result = []
        for profile in queryset:
            serializer = NetworkProfileSerializer(profile)
            json_profile = serializer.data

            # Create expanded host cred JSON
            expand_host_credential(profile, json_profile)

            result.append(json_profile)
        return Response(result)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a network profile."""
        response = super().create(request, args, kwargs)

        # Modify json for response
        json_profile = response.data
        profile = get_object_or_404(self.queryset, pk=json_profile['id'])

        # Create expanded host cred JSON
        expand_host_credential(profile, json_profile)
        return response

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        """Get a network profile."""
        profile = get_object_or_404(self.queryset, pk=pk)
        serializer = NetworkProfileSerializer(profile)
        json_profile = serializer.data

        # Create expanded host cred JSON
        expand_host_credential(profile, json_profile)

        return Response(json_profile)

    # pylint: disable=unused-argument
    def update(self, request, *args, **kwargs):
        """Update a network profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data,
                                         partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        json_profile = serializer.data

        # Create expanded host cred JSON
        expand_host_credential(profile, json_profile)

        return Response(json_profile)
