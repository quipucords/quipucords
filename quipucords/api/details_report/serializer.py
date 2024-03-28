"""Serializer for system facts models."""

from rest_framework.serializers import CharField, IntegerField, JSONField, UUIDField

from api.common.common_report import REPORT_TYPE_DETAILS
from api.common.serializer import NotEmptySerializer
from api.models import Report


class DetailsReportSerializer(NotEmptySerializer):
    """Serializer for the Details Report."""

    report_type = CharField(read_only=True, default=REPORT_TYPE_DETAILS)
    report_version = CharField(max_length=64, read_only=True)

    sources = JSONField()
    report_id = IntegerField(read_only=True, source="id")
    report_platform_id = UUIDField(format="hex_verbose", read_only=True)
    cached_csv = CharField(required=False, read_only=True)

    class Meta:
        """Meta class for DetailsReportSerializer."""

        model = Report
        exclude = ("id", "deployment_report")
