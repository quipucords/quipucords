"""Report serializers."""

from rest_framework.serializers import DictField, ModelSerializer

from api.models import InspectGroup, InspectResult


class InspectGroupSerializer(ModelSerializer):
    """InspectGroup Serializer."""

    class Meta:
        """Serializer config."""

        model = InspectGroup
        exclude = ["id", "created_at", "updated_at", "tasks"]


class InspectResultSerializer(ModelSerializer):
    """InspectResult Serializer."""

    raw_facts = DictField()
    metadata = InspectGroupSerializer(source="inspect_group")

    class Meta:
        """Serializer config."""

        model = InspectResult
        exclude = ["inspect_group"]
