"""Module for serializing all model object for database storage."""
from rest_framework.serializers import CharField, ChoiceField, JSONField

from api.common.serializer import NotEmptySerializer
from api.models import (
    InspectResult,
    JobInspectionResult,
    RawFact,
    TaskInspectionResult,
)


class RawFactSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    value = JSONField(required=True)

    class Meta:
        """Metadata for serializer."""

        model = RawFact
        fields = ["name", "value"]
        qpc_allow_empty_fields = []


class SystemInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    status = ChoiceField(required=True, choices=InspectResult.CONN_STATUS_CHOICES)

    class Meta:
        """Metadata for serializer."""

        model = InspectResult
        fields = ["name", "status", "source"]
        qpc_allow_empty_fields = ["source"]


class TaskInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the TaskInspectionResult model."""

    class Meta:
        """Metadata for serializer."""

        model = TaskInspectionResult
        fields = ["source", "systems"]
        qpc_allow_empty_fields = ["source", "systems"]


class JobInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the JobInspectionResult model."""

    class Meta:
        """Metadata for serializer."""

        model = JobInspectionResult
        fields = ["task_results"]
        qpc_allow_empty_fields = ["task_results"]
