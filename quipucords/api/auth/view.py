"""Viewset for auth function."""

import logging

from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api import messages
from api.auth.auth_lightspeed import lightspeed_auth_status, lightspeed_login_request
from api.auth.serializer import (
    AuthLoginResponseSerializer,
    AuthStatusResponseSerializer,
    FailedAuthRequestResponse,
)
from api.auth.utils import AuthError

logger = logging.getLogger(__name__)

SUPPORTED_AUTH_TYPES = ["lightspeed"]
SUPPORTED_AUTH_TYPES_STR = ", ".join(SUPPORTED_AUTH_TYPES)


def auth_valid_request(request, auth_type) -> tuple[bool, dict, int]:
    """Check if the request is valid."""
    if not auth_type:
        return (
            False,
            {"detail": _(messages.AUTH_MUST_SPECIFY_TYPE)},
            status.HTTP_400_BAD_REQUEST,
        )

    if auth_type not in SUPPORTED_AUTH_TYPES:
        return (
            False,
            {
                "detail": _(messages.AUTH_INVALID_AUTH_TYPE)
                % {
                    "auth_type": auth_type,
                    "supported_auth_types": SUPPORTED_AUTH_TYPES_STR,
                }
            },
            status.HTTP_400_BAD_REQUEST,
        )

    if not request.user or not request.user.is_authenticated:
        return (
            False,
            {"detail": _(messages.AUTH_MUST_BE_AUTHENTICATED)},
            status.HTTP_401_UNAUTHORIZED,
        )

    return True, {}, status.HTTP_200_OK


def bad_auth_response() -> OpenApiResponse:
    """Return an OpenApiResponse for a Bad Auth request."""
    return OpenApiResponse(
        description="Bad Auth Request response",
        response=FailedAuthRequestResponse(),
        examples=[
            OpenApiExample(
                "Bad Auth request",
                description="Bad Auth request response",
                value={"detail": _(messages.AUTH_MUST_SPECIFY_TYPE)},
            )
        ],
    )


def unauthorized_auth_response() -> OpenApiResponse:
    """Return an OpenApiResponse for an Unauthorized Auth request."""
    return OpenApiResponse(
        description="Unauthorized Auth Request response",
        response=FailedAuthRequestResponse(),
        examples=[
            OpenApiExample(
                "Unauthorized Auth request",
                description="Unauthorized Auth request response",
                value={"detail": _(messages.AUTH_MUST_BE_AUTHENTICATED)},
            )
        ],
    )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="auth_type",
            type=OpenApiTypes.STR,
            enum=SUPPORTED_AUTH_TYPES,
            description="The type of auth provider to login to (required)",
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Successful authorization request response",
            response=AuthLoginResponseSerializer(),
            examples=[
                OpenApiExample(
                    "Lightspeed Auth request response",
                    value={
                        "status": "pending",
                        "user_code": "ABCD-EFGH",
                        "verification_uri": "https://auth.example.com/device",
                        "verification_uri_complete": "https://auth.example.com/device?user_code=ABCD-EFGH",
                    },
                )
            ],
        ),
        (400, "application/json"): bad_auth_response(),
        (401, "application/json"): unauthorized_auth_response(),
    },
)
@api_view(["post"])
@renderer_classes([JSONRenderer])
def auth_login(request):
    """Do an Authentication Login for the current user."""
    auth_type = request.GET.get("auth_type", None)

    is_valid, response_data, response_status = auth_valid_request(request, auth_type)
    if not is_valid:
        return Response(response_data, status=response_status)

    try:
        data = lightspeed_login_request(request.user)
    except AuthError as err:
        return Response(
            {"detail": err.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="auth_type",
            type=OpenApiTypes.STR,
            enum=SUPPORTED_AUTH_TYPES,
            description="The type of auth to request status of (required)",
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Successful authorization request status response",
            response=AuthStatusResponseSerializer(),
            examples=[
                OpenApiExample(
                    "Missing Auth status response",
                    value={"status": "missing"},
                ),
                OpenApiExample(
                    "Lightspeed Auth status response",
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
                    "Expired Lightspeed Auth status response",
                    value={
                        "status": "expired",
                        "metadata": {
                            "status": "expired",
                            "status_reason": (
                                "Authorization token expired,"
                                " please re-login to Lightspeed"
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
        (400, "application/json"): bad_auth_response(),
        (401, "application/json"): unauthorized_auth_response(),
    },
)
@api_view(["get"])
@renderer_classes([JSONRenderer])
def auth_status(request):
    """Request the status about an Authentication for the current user."""
    auth_type = request.GET.get("auth_type", None)

    is_valid, response_data, response_status = auth_valid_request(request, auth_type)
    if not is_valid:
        return Response(response_data, status=response_status)

    try:
        data = lightspeed_auth_status(request.user)
    except AuthError as err:
        return Response(
            {"detail": err.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(data, status=status.HTTP_200_OK)
