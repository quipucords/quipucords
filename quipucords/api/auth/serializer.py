"""Serializers for auth API endpoints."""

from rest_framework import serializers


class AuthLoginResponseSerializer(serializers.Serializer):
    """Define a serializer for successful auth login response."""

    status = serializers.CharField(required=True)
    user_code = serializers.CharField(required=False)
    verification_uri = serializers.CharField(required=False)
    verification_uri_complete = serializers.CharField(required=False)


class AuthStatusResponseSerializer(serializers.Serializer):
    """Define a Serializer for successful auth status response."""

    status = serializers.CharField(required=True)
    metadata = serializers.DictField(required=False)


class FailedAuthRequestResponse(serializers.Serializer):
    """Define a Serializer for a failed auth request response."""

    detail = serializers.CharField(required=True)
