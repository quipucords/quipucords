"""Viewset for user function."""
import logging

from django.contrib.auth import logout
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.GenericViewSet):
    """User view for logout and user data."""

    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get the username of currently authenticated user."""
        return Response({"username": request.user.username})

    @action(detail=False, methods=["put"])
    def logout(self, request):
        """Log out the current authenticated user."""
        if user := request.user:
            Token.objects.filter(user=user).all().delete()
        logout(request)
        return Response(headers={"Clear-Site-Data": '"cookies", "storage"'})
