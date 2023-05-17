"""Viewset for user function."""
import logging

from django.contrib.auth import logout
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.user.authentication import QuipucordsExpiringTokenAuthentication

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class UserViewSet(viewsets.GenericViewSet):
    """User view for logout and user data."""

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
        instance = request.user
        logout(request)
        token = Token.objects.filter(user=instance).first()
        if token:
            token.delete()
        if instance:
            token = Token.objects.create(user=instance)

        return Response()
