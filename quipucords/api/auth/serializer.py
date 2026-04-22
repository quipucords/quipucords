"""Common Serializers for the auth API endpoints."""

from rest_framework import serializers


class FailedAuthRequestResponseSerializer(serializers.Serializer):
    """Define a Serializer for a failed auth request response."""

    detail = serializers.CharField(required=True)
