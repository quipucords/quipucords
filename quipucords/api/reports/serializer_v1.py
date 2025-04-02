"""Serializers for reports."""

import re

from django.db import transaction
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DictField,
    ListField,
    Serializer,
    UUIDField,
    ValidationError,
)

from api.models import (
    Report,
    ScanJob,
    ScanTask,
)
from constants import MINIMUM_REPORT_VERSION, DataSources


class SourceSerializer(Serializer):
    """Serializer for 'details report' sources."""

    server_id = UUIDField()
    report_version = CharField()
    source_name = CharField()
    source_type = ChoiceField(choices=DataSources.choices)
    facts = ListField(child=DictField(), min_length=1)

    def validate_report_version(self, value):
        """Validate report version."""
        regex_match = re.match(r"(\d+)\.(\d+)\.(\d+)\+\S", value)
        if not regex_match:
            raise ValidationError("Invalid report_version.")
        source_version = tuple(map(int, regex_match.groups()))
        if source_version < MINIMUM_REPORT_VERSION:
            source_version_str = ".".join(map(str, source_version))
            minimum_version_str = ".".join(map(str, MINIMUM_REPORT_VERSION))
            raise ValidationError(
                f"Source version ({source_version_str}) is below the minimum "
                f"supported report version ({minimum_version_str})"
            )
        return value


class ReportUploadSerializer(Serializer):
    """Serializer for uploaded details reports."""

    report_type = ChoiceField(choices=["details"])
    sources = SourceSerializer(many=True)

    def validate_sources(self, value):
        """Validate sources."""
        if len(value) == 0:
            raise ValidationError("minimum length required for 'sources' is 1.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create a report filled with raw data and a fingerprint-type ScanJob."""
        report = Report.objects.create()
        # create a scan job and required scan tasks for a "upload" job
        scan_job = ScanJob.objects.create(
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            report=report,
        )
        scan_job.ingest_sources(validated_data["sources"])
        return report
