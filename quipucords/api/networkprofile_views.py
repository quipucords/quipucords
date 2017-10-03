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
"""Describes the views associatd with the API models"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
from api.filters import ListFilter
from api.networkprofile_serializer import NetworkProfileSerializer
from api.networkprofile_model import NetworkProfile


class NetworkProfileFilter(FilterSet):
    """Filter for network profiles by name"""
    name = ListFilter(name='name')

    class Meta:
        model = NetworkProfile
        fields = ['name']


# pylint: disable=too-many-ancestors
class NetworkProfileViewSet(ModelViewSet):
    """A view set for NetworkProfiles"""

    queryset = NetworkProfile.objects.all()
    serializer_class = NetworkProfileSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = NetworkProfileFilter

    def list(self, request):  # pylint: disable=unused-argument
        queryset = self.filter_queryset(self.get_queryset())
        serializer = NetworkProfileSerializer(queryset, many=True)
        return Response(serializer.data)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        network_profile = get_object_or_404(self.queryset, pk=pk)
        serializer = NetworkProfileSerializer(network_profile)
        return Response(serializer.data)

    # pylint: disable=unused-argument
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
