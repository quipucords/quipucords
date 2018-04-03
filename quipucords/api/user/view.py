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

"""Viewset for user function."""
import logging
import os

from django.contrib.auth import logout

from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class UserViewSet(viewsets.GenericViewSet):
    """User view for logout and user data."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    @list_route(methods=['get'])
    def current(self, request):  # pylint: disable=R0201
        """Get the username of currently authenticated user."""
        return Response({'username': request.user.username})

    @list_route(methods=['put'])
    def logout(self, request):  # pylint: disable=R0201
        """Log out the current authenticated user."""
        instance = request.user
        logout(request)
        token = Token.objects.filter(user=instance).first()
        if token:
            token.delete()
        if instance:
            token = Token.objects.create(user=instance)

        return Response()
