"""Viewset for auth function."""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api import messages
from api.auth.auth_hashicorp_vault import (
    HashiCorpVaultAuthError,
    delete_hashicorp_vault_token,
    get_hashicorp_vault_token,
)
from api.auth.auth_lightspeed import (
    LightspeedAuthError,
    lightspeed_login_request,
    lightspeed_logout_request,
    user_lightspeed_auth_status,
)
from api.auth.serializer import (
    FailedAuthRequestResponseSerializer,
    HashiCorpVaultResponseSerializer,
    HashiCorpVaultSerializer,
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


def hashicorp_vault_not_defined() -> OpenApiResponse:
    """Return an OpenApiResponse if the HashiCorp Vault is not defined (404)."""
    return OpenApiResponse(
        description="HashiCorp Vault server not found response.",
        response=FailedAuthRequestResponseSerializer(),
        examples=[
            OpenApiExample(
                "HashiCorp Vault server not found response.",
                description="HashiCorp Vault server is not defined",
                value={"detail": "HashiCorp Vault server is not defined"},
            )
        ],
    )


def hashicorp_vault_missing_client_key() -> OpenApiResponse:
    """Return an OpenApiResponse if the HashiCorp Vault is missing client_key."""
    return OpenApiResponse(
        description="HashiCorp Vault server definition is missing client_key.",
        response=FailedAuthRequestResponseSerializer(),
        examples=[
            OpenApiExample(
                "HashiCorp Vault server is missing client_key.",
                description="HashiCorp Vault server is missing client_key defined",
                value={"client_key": ["This field is required."]},
            )
        ],
    )


def hashicorp_vault_port_not_integer() -> OpenApiResponse:
    """Return an OpenApiResponse if the HashiCorp Vault port is not an integer."""
    return OpenApiResponse(
        description="HashiCorp Vault server port is not an integer.",
        response=FailedAuthRequestResponseSerializer(),
        examples=[
            OpenApiExample(
                "HashiCorp Vault server port is not an integer.",
                description="HashiCorp Vault server port is not an integer.",
                value={"port": ["A valid integer is required."]},
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
    serializer = lightspeed_logout_request(request.user)
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
    serializer = user_lightspeed_auth_status(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


class HashiCorpVaultViewSet(viewsets.GenericViewSet):
    """A view set for the hashicorp-vault auth endpoint.

    This is a singleton resource, so it doesn't use standard pk-based routing.
    All operations work on the single HashiCorp Vault configuration.
    """

    serializer_class = HashiCorpVaultSerializer

    @extend_schema(
        responses={
            (200, "application/json"): OpenApiResponse(
                description="Successful HashiCorp Vault server retrieved",
                response=HashiCorpVaultResponseSerializer(),
                examples=[
                    OpenApiExample(
                        "HashiCorp Vault Server definition",
                        value={
                            "address": "vault.example.com",
                            "port": 8200,
                            "ssl_verify": False,
                        },
                    )
                ],
            ),
            (401, "application/json"): unauthorized_auth_response(),
            (404, "application/json"): hashicorp_vault_not_defined(),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get the HashiCorp Vault server definition."""
        hashicorp_vault_token = get_hashicorp_vault_token()
        if hashicorp_vault_token is None:
            return Response(
                {"detail": _(messages.HASHICORP_VAULT_NOT_DEFINED)},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=hashicorp_vault_token.metadata)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OpenApiRequest(
            HashiCorpVaultSerializer(),
            examples=[
                OpenApiExample(
                    "Request to define a HashiCorp Vault server",
                    description="HashiCorp Vault server definition with a client"
                    " certificate and key. client_cert and client_key are single line"
                    " base64 encodings of the certificate pem files.",
                    value={
                        "address": "vault.example.com",
                        "port": 8200,
                        "ssl_verify": False,
                        "client_cert": "....",
                        "client_key": "....",
                    },
                    request_only=True,
                ),
            ],
        ),
        responses={
            (201, "application/json"): OpenApiResponse(
                description="Successful HashiCorp Vault server created",
                response=HashiCorpVaultResponseSerializer(),
                examples=[
                    OpenApiExample(
                        "HashiCorp Vault Server definition",
                        value={
                            "address": "vault.example.com",
                            "port": 8200,
                            "ssl_verify": False,
                        },
                    )
                ],
            ),
            (401, "application/json"): unauthorized_auth_response(),
            (400, "application/json"): hashicorp_vault_missing_client_key(),
            (409, "application/json"): OpenApiResponse(
                description="HashiCorp Vault server already exists.",
                response=FailedAuthRequestResponseSerializer(),
                examples=[
                    OpenApiExample(
                        "HashiCorp Vault server already exists.",
                        description="HashiCorp Vault server definition already exists",
                        value={
                            "detail": "HashiCorp Vault server definition already exists"
                        },
                    )
                ],
            ),
        },
    )
    def create(self, request, *args, **kwargs) -> Response:
        """Create a HashiCorp Vault server definition."""
        if get_hashicorp_vault_token():
            return Response(
                {"detail": _(messages.HASHICORP_VAULT_ALREADY_EXISTS)},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except HashiCorpVaultAuthError as err:
            return Response(
                {"detail": _(err.message)}, status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as err:
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=OpenApiRequest(
            HashiCorpVaultSerializer(),
            examples=[
                OpenApiExample(
                    "Request to replace the HashiCorp Vault server definition",
                    description="HashiCorp Vault server definition with a client"
                    " certificate, key and CA cert. client_cert, client_key and"
                    " ca_cert are single line base64 encoded of the certificate"
                    " pem files.",
                    value={
                        "address": "newvault.example.com",
                        "port": 8210,
                        "ssl_verify": True,
                        "client_cert": "....",
                        "client_key": "....",
                        "ca_cert": "....",
                    },
                    request_only=True,
                ),
            ],
        ),
        responses={
            (200, "application/json"): OpenApiResponse(
                description="Successful update of the HashiCorp Vault server",
                response=HashiCorpVaultResponseSerializer(),
                examples=[
                    OpenApiExample(
                        "Updated HashiCorp Vault server definition",
                        value={
                            "address": "newvault.example.com",
                            "port": 8210,
                            "ssl_verify": True,
                        },
                    )
                ],
            ),
            (401, "application/json"): unauthorized_auth_response(),
            (400, "application/json"): hashicorp_vault_missing_client_key(),
            (404, "application/json"): hashicorp_vault_not_defined(),
        },
    )
    def update(self, request, *args, **kwargs) -> Response:
        """Update a HashiCorp Vault server definition."""
        partial = kwargs.pop("partial", False)

        hashicorp_vault_token = get_hashicorp_vault_token()
        if hashicorp_vault_token is None:
            return Response(
                {"detail": _(messages.HASHICORP_VAULT_NOT_DEFINED)},
                status=status.HTTP_404_NOT_FOUND,
            )

        if partial:
            metadata = hashicorp_vault_token.metadata | request.data
        else:
            metadata = request.data

        serializer = self.serializer_class(
            instance=hashicorp_vault_token, data=metadata, partial=partial
        )
        try:
            serializer.is_valid(raise_exception=True)
        except HashiCorpVaultAuthError as err:
            return Response(
                {"detail": _(err.message)}, status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as err:
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        request=OpenApiRequest(
            HashiCorpVaultSerializer(),
            examples=[
                OpenApiExample(
                    "Request to update the port of a HashiCorp Vault server",
                    description="Updated HashiCorp Vault server port.",
                    value={
                        "port": 8230,
                    },
                    request_only=True,
                ),
            ],
        ),
        responses={
            (200, "application/json"): OpenApiResponse(
                description="Successful HashiCorp Vault server updated",
                response=HashiCorpVaultResponseSerializer(),
                examples=[
                    OpenApiExample(
                        "HashiCorp Vault Server definition",
                        value={
                            "address": "newvault.example.com",
                            "port": 8230,
                            "ssl_verify": True,
                        },
                    )
                ],
            ),
            (401, "application/json"): unauthorized_auth_response(),
            (400, "application/json"): hashicorp_vault_port_not_integer(),
            (404, "application/json"): hashicorp_vault_not_defined(),
        },
    )
    def partial_update(self, request, *args, **kwargs) -> Response:
        """Do a partial update (PATCH) of the HashiCorp Vault server definition."""
        return self.update(request, partial=True)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete the HashiCorp Vault Singleton server definition."""
        delete_hashicorp_vault_token()
        return Response(status=status.HTTP_204_NO_CONTENT)
