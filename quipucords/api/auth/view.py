"""Viewset for auth function."""

import logging

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.auth.auth_insights import insights_login

logger = logging.getLogger(__name__)

SUPPORTED_AUTH_TYPES = ["insights"]


@api_view(["post"])
@renderer_classes([JSONRenderer])
def auth_login(request):
    """Do an Authentication Login for the current user."""
    auth_type = request.GET.get("auth_type", None)

    if not auth_type:
        return Response(
            _("Must specify an auth_type"), status=status.HTTP_400_BAD_REQUEST
        )

    if auth_type not in SUPPORTED_AUTH_TYPES:
        return Response(
            _(
                "Invalid auth_type %(auth_type)s specified,"
                " must be one of %(supported_auth_types)s."
            )
            % {
                "auth_type": auth_type,
                "supported_auth_types": ", ".join(SUPPORTED_AUTH_TYPES),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if user := request.user:
        print(f"AHA!!!! doing an /auth/login for user {user.username}")

    data = insights_login(user)
    return Response(data, status=status.HTTP_200_OK)
