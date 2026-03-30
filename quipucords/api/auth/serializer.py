"""Serializers for auth API endpoints."""

from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from api.auth.auth_hashicorp_vault import (
    HashiCorpVaultAuthError,
    decode_cert_from_content,
    get_or_create_hashicorp_vault_token,
    hashicorp_vault_authenticate,
    hashicorp_vault_url,
)


class HashiCorpVaultSerializer(serializers.Serializer):
    """Define a serializer for the HashiCorp Vault API."""

    address = serializers.CharField(required=True)
    port = serializers.IntegerField(required=False, default=8200)
    ssl_verify = serializers.BooleanField(required=False, default=True)
    client_key = serializers.CharField(required=True)
    client_cert = serializers.CharField(required=True)
    ca_cert = serializers.CharField(required=False)

    class Meta:
        """Metadata for the serializer."""

        # Note: exclude only works with Model serializers, removing them manually
        #       in the to_representation method.
        exclude = ["client_key", "client_cert", "ca_cert"]

    def is_valid(self, raise_exception=False):
        """Ensure that HashiCorp Vault is valid."""
        return super().is_valid(raise_exception=raise_exception)

    @transaction.atomic
    def create(self, validated_data):
        """Create and return a HashiCorp Vault object."""
        secure_token = get_or_create_hashicorp_vault_token()
        secure_token.token = None
        secure_token.metadata = validated_data
        secure_token.save()
        return secure_token

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update and return a HashiCorp Vault object."""
        instance.metadata = validated_data
        instance.save()
        return instance

    def to_representation(self, instance):
        """Generate HashiCorp Vault server definition based on SecureToken object."""
        if isinstance(instance, dict):
            data = super().to_representation(instance)
        else:
            data = super().to_representation(instance.metadata)
        for sensitive_attr in self.Meta.exclude:
            data.pop(sensitive_attr, None)
        return data

    @staticmethod
    def verify_client_cert_is_base64encoded(cert_file_name, value):
        """Verify the cert specific is properly base64 encoded."""
        try:
            decode_cert_from_content(cert_file_name, value)
        except ValueError as err:
            raise ValidationError(err)
        return value

    def validate_client_cert(self, value):
        """Validate the client certificate is valid."""
        return self.verify_client_cert_is_base64encoded("client_cert", value)

    def validate_client_key(self, value):
        """Validate the client key is valid."""
        return self.verify_client_cert_is_base64encoded("client_key", value)

    def validate_ca_cert(self, value):
        """Validate the CA certificate is valid."""
        return self.verify_client_cert_is_base64encoded("ca_cert", value)

    def validate(self, data):
        """Validate the data is valid and we can communicate with HashiCorp Vault."""
        attrs = super().validate(data)

        errors = {}
        ssl_verify = attrs.get("ssl_verify", True)
        if ssl_verify and attrs.get("ca_cert", None) is None:
            errors["ca_cert"] = "Must specify a ca_cert with ssl_verify is True"

        if errors:
            raise ValidationError(errors)

        try:
            if not hashicorp_vault_authenticate(metadata=attrs):
                vault_url = hashicorp_vault_url(attrs)
                raise ValidationError(
                    f"Failed to authenticate with HashiCorp Vault {vault_url}"
                )
        except HashiCorpVaultAuthError as err:
            raise ValidationError(err.message)

        return attrs


class LightspeedAuthLoginResponseSerializer(serializers.Serializer):
    """Define a serializer for successful auth login response."""

    status = serializers.CharField(required=True)
    user_code = serializers.CharField(required=False)
    verification_uri = serializers.CharField(required=False)
    verification_uri_complete = serializers.CharField(required=False)


class LightspeedAuthLogoutResponseSerializer(serializers.Serializer):
    """Define a serializer for auth logout response."""

    status = serializers.CharField(required=True)
    status_reason = serializers.CharField(required=False)


class LightspeedAuthStatusMetadataSerializer(serializers.Serializer):
    """Define a serializer for the Lightspeed auth status metadata."""

    # Note: In the Lightspeed Identity Schema, org_id and
    #       account_number are defined as strings.
    status = serializers.CharField(required=True)
    status_reason = serializers.CharField(required=False)
    org_id = serializers.CharField(required=False)
    account_number = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)


class LightspeedAuthStatusResponseSerializer(serializers.Serializer):
    """Define a Serializer for successful auth status response."""

    status = serializers.CharField(required=True)
    metadata = LightspeedAuthStatusMetadataSerializer(required=False)


class FailedAuthRequestResponseSerializer(serializers.Serializer):
    """Define a Serializer for a failed auth request response."""

    detail = serializers.CharField(required=True)
