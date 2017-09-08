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

from rest_framework.viewsets import ModelViewSet
from api.serializers import CredentialSerializer, HostCredentialSerializer
from api.models import Credential, HostCredential


class CredentialViewSet(ModelViewSet):
    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer


class HostCredentialViewSet(ModelViewSet):
    queryset = HostCredential.objects.all()
    serializer_class = HostCredentialSerializer
