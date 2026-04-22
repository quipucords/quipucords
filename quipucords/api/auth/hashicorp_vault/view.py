"""Viewset for the HashiCorp Vault auth API endpoint."""

import logging

from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api import messages
from api.auth.common import unauthorized_auth_response
from api.auth.hashicorp_vault.auth import (
    HashiCorpVaultAuthError,
    delete_hashicorp_vault_token,
    get_hashicorp_vault_token,
)
from api.auth.hashicorp_vault.serializer import (
    HashiCorpVaultResponseSerializer,
    HashiCorpVaultSerializer,
)
from api.auth.serializer import (
    FailedAuthRequestResponseSerializer,
)

logger = logging.getLogger(__name__)


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


class HashiCorpVaultViewSet(viewsets.GenericViewSet):
    """A view set for the hashicorp-vault auth endpoint.

    This is a singleton resource, so it doesn't use standard pk-based routing.
    All operations work on the single HashiCorp Vault configuration.
    """

    serializer_class = HashiCorpVaultSerializer
    response_serializer_class = HashiCorpVaultResponseSerializer

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
    def list(self, request, *args, **kwargs) -> Response:
        """Get the HashiCorp Vault server definition."""
        hashicorp_vault_token = get_hashicorp_vault_token()
        if hashicorp_vault_token is None:
            return Response(
                {"detail": _(messages.HASHICORP_VAULT_NOT_DEFINED)},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.response_serializer_class(data=hashicorp_vault_token.metadata)
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
    def post(self, request, *args, **kwargs) -> Response:
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
        serializer.save()
        response_serializer = self.response_serializer_class(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

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
    def put(self, request, *args, **kwargs) -> Response:
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
            return Response(err.detail, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        response_serializer = self.response_serializer_class(serializer.data)
        return Response(response_serializer.data)

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
    def patch(self, request, *args, **kwargs) -> Response:
        """Do a partial update (PATCH) of the HashiCorp Vault server definition."""
        return self.put(request, partial=True)

    @transaction.atomic
    def delete(self, request, *args, **kwargs) -> Response:
        """Delete the HashiCorp Vault Singleton server definition."""
        delete_hashicorp_vault_token()
        return Response(status=status.HTTP_204_NO_CONTENT)
