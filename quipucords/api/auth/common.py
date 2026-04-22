"""Common functions for the auth API endpoints."""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
)

from api.auth.serializer import FailedAuthRequestResponseSerializer


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
