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
        except self.get_model().DoesNotExist as exception:
            raise exceptions.AuthenticationFailed("Invalid token") from exception

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")

        utc_now = datetime.datetime.utcnow()

        hours = settings.QPC_TOKEN_EXPIRE_HOURS
        if token.created < utc_now - datetime.timedelta(hours=hours):
            raise exceptions.AuthenticationFailed("Token has expired")

        return (token.user, token)
