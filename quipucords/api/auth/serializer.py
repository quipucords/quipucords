"""Serializers for auth API endpoints."""

from rest_framework import serializers


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
