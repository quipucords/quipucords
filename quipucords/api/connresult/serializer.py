"""Module for serializing all model object for database storage."""


from rest_framework.serializers import CharField, ChoiceField

from api.common.serializer import NotEmptySerializer
from api.models import JobConnectionResult, SystemConnectionResult, TaskConnectionResult


class SystemConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemConnectionResult model."""

    name = CharField(required=True)
    status = ChoiceField(
        required=True, choices=SystemConnectionResult.CONN_STATUS_CHOICES
    )

    class Meta:
        """Metadata for serializer."""

        model = SystemConnectionResult
        fields = ["name", "status", "source", "credential"]
        qpc_allow_empty_fields = ["value", "source"]


class TaskConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the TaskConnectionResult model."""

    class Meta:
        """Metadata for serializer."""

        model = TaskConnectionResult
        fields = ["source", "systems"]
        qpc_allow_empty_fields = ["source", "systems"]


class JobConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the JobConnectionResult model."""

    class Meta:
        """Metadata for serializer."""

        model = JobConnectionResult
        fields = ["task_results"]
        qpc_allow_empty_fields = ["task_results"]
