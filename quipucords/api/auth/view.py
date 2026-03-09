"""Viewset for auth function."""

import logging

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.auth.auth_insights import insights_auth_status, insights_login_request
from api.auth.utils import AuthError

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

    try:
        data = insights_login_request(request.user)
    except AuthError as err:
        return Response(
            {"detail": err.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(data, status=status.HTTP_200_OK)


@api_view(["get"])
@renderer_classes([JSONRenderer])
def auth_status(request):
    """Request the status about an Authentication for the current user."""
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

    try:
        data = insights_auth_status(request.user)
    except AuthError as err:
        return Response(
            {"detail": err.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(data, status=status.HTTP_200_OK)
