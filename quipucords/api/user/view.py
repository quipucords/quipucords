#
# Copyright (c) 2018-2019 Red Hat, Inc.
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

from api.user.authentication import QuipucordsExpiringTokenAuthentication

from django.contrib.auth import logout

from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class UserViewSet(viewsets.GenericViewSet):
    """User view for logout and user data."""

    authentication_enabled = os.getenv("QPC_DISABLE_AUTHENTICATION") != "True"
    if authentication_enabled:
        authentication_classes = (
            QuipucordsExpiringTokenAuthentication,
            SessionAuthentication,
        )
        permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get the username of currently authenticated user."""
        return Response({"username": request.user.username})

    @action(detail=False, methods=["put"])
    def logout(self, request):
        """Log out the current authenticated user."""
        authentication_enabled = os.getenv("QPC_DISABLE_AUTHENTICATION") != "True"
        if not authentication_enabled:
            return Response()
        instance = request.user
        logout(request)
        token = Token.objects.filter(user=instance).first()
        if token:
            token.delete()
        if instance:
            token = Token.objects.create(user=instance)

        return Response()
