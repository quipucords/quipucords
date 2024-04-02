"""Expiring authorization token."""

import datetime

from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


class QuipucordsExpiringAuthToken(ObtainAuthToken):
    """Expiring token implementation."""

    def post(self, request, *args, **kwargs):
        """Create and retrieve token."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        auth_token, created = Token.objects.get_or_create(user=user)

        utc_now = datetime.datetime.utcnow()
        valid_token_window = utc_now - datetime.timedelta(
            hours=settings.QPC_TOKEN_EXPIRE_HOURS
        )
        if not created and auth_token.created < valid_token_window:
            # refresh the token
            auth_token.delete()
            auth_token = Token.objects.create(user=user)
            auth_token.created = datetime.datetime.utcnow()
            auth_token.save()

        return Response({"token": auth_token.key})


QuipucordsExpiringAuthTokenView = QuipucordsExpiringAuthToken.as_view()
