"""Viewset for auth function."""

import logging

from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.auth.auth_lightspeed import (
    LightspeedAuthError,
    lightspeed_login_request,
    lightspeed_logout_request,
    user_lightspeed_auth_status,
)
from api.auth.serializer import (
    FailedAuthRequestResponseSerializer,
    LightspeedAuthLoginResponseSerializer,
    LightspeedAuthLogoutResponseSerializer,
    LightspeedAuthStatusResponseSerializer,
)

logger = logging.getLogger(__name__)


def unauthorized_auth_response() -> OpenApiResponse:
    """Return an OpenApiResponse for an unauthorized auth request."""
    return OpenApiResponse(
        description="Unauthorized auth request response",
        response=FailedAuthRequestResponseSerializer(),
        examples=[
            OpenApiExample(
                "Unauthorized auth request response",
                description="Unauthorized auth request response",
                value={"detail": "Authentication credentials were not provided."},
            )
        ],
    )


@extend_schema(
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Successful Lightspeed login request response",
            response=LightspeedAuthLoginResponseSerializer(),
            examples=[
                OpenApiExample(
                    "Lightspeed login request response",
                    value={
                        "status": "pending",
                        "user_code": "ABCD-EFGH",
                        "verification_uri": "https://auth.example.com/device",
                        "verification_uri_complete": "https://auth.example.com/device?user_code=ABCD-EFGH",
                    },
                )
            ],
        ),
        (401, "application/json"): unauthorized_auth_response(),
    },
)
@api_view(["post"])
@renderer_classes([JSONRenderer])
def lightspeed_auth_login(request):
    """Do an Authentication Login for the current user."""
    try:
        serializer = lightspeed_login_request(request.user)
    except LightspeedAuthError as err:
        return Response(
            {"detail": _(err.message)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Successful logout response",
            response=LightspeedAuthLogoutResponseSerializer(),
            examples=[
                OpenApiExample(
                    "Lightspeed logout response",
                    value={
                        "status": "successful",
                        "status_reason": "Already logged out",
                    },
                )
            ],
        ),
        (401, "application/json"): unauthorized_auth_response(),
    },
)
@api_view(["post"])
@renderer_classes([JSONRenderer])
def lightspeed_auth_logout(request):
    """Do an Authentication Logout for the current user."""
    try:
        serializer = lightspeed_logout_request(request.user)
    except LightspeedAuthError as err:
        return Response(
            {"detail": _(err.message)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Successful Lightspeed authorization status request responses",
            response=LightspeedAuthStatusResponseSerializer(),
            examples=[
                OpenApiExample(
                    "Missing Lightspeed auth status response",
                    value={"status": "missing"},
                ),
                OpenApiExample(
                    "Valid Lightspeed auth status response",
                    value={
                        "status": "valid",
                        "metadata": {
                            "status": "valid",
                            "status_reason": "",
                            "org_id": "123456",
                            "account_number": "4567890",
                            "username": "jdoe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "jdoe@example.com",
                        },
                    },
                ),
                OpenApiExample(
                    "Expired Lightspeed auth status response",
                    value={
                        "status": "expired",
                        "metadata": {
                            "status": "expired",
                            "status_reason": (
                                "Authorization token expired,"
                                " please login again to Lightspeed"
                            ),
                            "org_id": "123456",
                            "account_number": "4567890",
                            "username": "jdoe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "jdoe@example.com",
                        },
                    },
                ),
            ],
        ),
        (401, "application/json"): unauthorized_auth_response(),
    },
)
@api_view(["get"])
@renderer_classes([JSONRenderer])
def lightspeed_auth_status(request):
    """Request the status about a Lightspeed Authentication for the current user."""
    try:
        serializer = user_lightspeed_auth_status(request.user)
    except LightspeedAuthError as err:
        return Response(
            {"detail": _(err.message)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(serializer.data, status=status.HTTP_200_OK)
