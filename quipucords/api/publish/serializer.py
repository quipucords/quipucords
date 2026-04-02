"""Serializers for publish requests."""

from rest_framework.serializers import ModelSerializer

from api.publish.model import PublishRequest


class PublishRequestSerializer(ModelSerializer):
    """Read-only serializer for PublishRequest."""

    class Meta:
        """Serializer config."""

        model = PublishRequest
        fields = [
            "report_id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
