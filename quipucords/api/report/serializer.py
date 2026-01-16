"""Report serializers."""

from rest_framework.serializers import DictField, ModelSerializer, ReadOnlyField

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
        ]
