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
from django.shortcuts import get_object_or_404
from api.scanjob_model import ScanJob
from api.scanjob_serializer import ScanJobSerializer
from api.networkprofile_model import NetworkProfile


PROFILE_KEY = 'profile'


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
