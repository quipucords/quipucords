"""Serializer for system facts models."""

from rest_framework.serializers import CharField, IntegerField, UUIDField

from api.common.serializer import CustomJSONField, NotEmptySerializer
from api.models import DetailsReport


class DetailsReportSerializer(NotEmptySerializer):
    """Serializer for the DetailsReport model."""

    report_type = CharField(read_only=True)
    report_version = CharField(max_length=64, read_only=True)

    sources = CustomJSONField(required=True)
    report_id = IntegerField(read_only=True)
    report_platform_id = UUIDField(format="hex_verbose", read_only=True)
    cached_csv = CharField(required=False, read_only=True)
    cached_masked_csv = CharField(required=False, read_only=True)

    class Meta:
        """Meta class for DetailsReportSerializer."""

        model = DetailsReport
        exclude = ("id", "deployment_report")
