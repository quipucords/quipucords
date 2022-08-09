#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Expiring token authorization."""

import datetime
import os

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class QuipucordsExpiringTokenAuthentication(TokenAuthentication):
    """Expiring token authorization."""

    def authenticate_credentials(self, key):
        """Authenticate token."""
        authentication_enabled = os.getenv("QPC_DISABLE_AUTHENTICATION") != "True"
        if not authentication_enabled:
            # skip this without authentication
            return None
        try:
            token = self.get_model().objects.get(key=key)
        except self.get_model().DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")

        utc_now = datetime.datetime.utcnow()

        hours = settings.QPC_TOKEN_EXPIRE_HOURS
        if token.created < utc_now - datetime.timedelta(hours=hours):
            raise exceptions.AuthenticationFailed("Token has expired")

        return (token.user, token)
