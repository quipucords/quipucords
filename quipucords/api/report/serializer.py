"""Report serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework.serializers import (
    DictField,
    ModelSerializer,
    ReadOnlyField,
    SerializerMethodField,
)

from api.common.enumerators import (
    LightspeedCannotPublishReason,
    ReportCannotDownloadReason,
)
from api.models import InspectGroup, InspectResult, Report


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


class ReportSerializer(ModelSerializer):
    """Report Serializer."""

    scan_id = ReadOnlyField(source="scanjob.scan_id")
    cannot_publish_reason = SerializerMethodField()
    cannot_download_reason = SerializerMethodField()

    class Meta:
        """Serializer config."""

        model = Report
        fields = [
            "id",
            "created_at",
            "updated_at",
            "report_version",
            "report_platform_id",
            "origin",
            "scan_id",
            "can_publish",
            "cannot_publish_reason",
            "can_download",
            "cannot_download_reason",
        ]

    @extend_schema_field(LightspeedCannotPublishReason)
    def get_cannot_publish_reason(self, obj):
        """Calculate `cannot_publish_reason` value.

        Note argument is entire instance (not field value), and return value
        must be JSON-serializable.
        """
        if reason := obj.cannot_publish_reason:
            return reason.value
        return None

    @extend_schema_field(ReportCannotDownloadReason)
    def get_cannot_download_reason(self, obj):
        """Calculate `cannot_download_reason` value."""
        if reason := obj.cannot_download_reason:
            return reason.value
        return None
