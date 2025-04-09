"""Scanjob related serializers."""

from rest_framework.serializers import IntegerField, ModelSerializer

from api.models import ScanJob, Source


class InternalSourceSerializer(ModelSerializer):
    """Summarized source serializer for ScanJobSerializer."""

    class Meta:
        """Serializer metadata."""

        model = Source
        fields = ["id", "name", "source_type"]


class ScanJobSerializer(ModelSerializer):
    """ScanJob serializer."""

    sources = InternalSourceSerializer(many=True)
    systems_count = IntegerField(read_only=True)
    systems_scanned = IntegerField(read_only=True)
    systems_failed = IntegerField(read_only=True)
    systems_unreachable = IntegerField(read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = [
            "id",
            "scan_id",
            "report_id",
            "scan_type",
            "status",
            "status_message",
            "start_time",
            "end_time",
            "sources",
            "systems_count",
            "systems_scanned",
            "systems_failed",
            "systems_unreachable",
        ]
