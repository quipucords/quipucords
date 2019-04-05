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

"""Expiring authorization token."""
import datetime


from django.conf import settings

import pytz

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


TOKEN_TTL_HOURS = getattr(settings, 'REST_FRAMEWORK_TOKEN_EXPIRE_HOURS', 24)


class QuipucordsExpiringAuthToken(ObtainAuthToken):
    """Expiring token implementation."""

    def post(self, request, *args, **kwargs):
        """Create and retrieve token."""
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        auth_token, created = Token.objects.get_or_create(user=user)

        utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        valid_token_window = \
            utc_now - datetime.timedelta(hours=TOKEN_TTL_HOURS)
        if not created and \
                auth_token.created < valid_token_window:
            # refresh the token
            auth_token.delete()
            auth_token = Token.objects.create(user=user)
            auth_token.created = datetime.datetime.utcnow()
            auth_token.save()

        return Response({'token': auth_token.key})


# pylint: disable=invalid-name
QuipucordsExpiringAuthTokenView = QuipucordsExpiringAuthToken.as_view()
