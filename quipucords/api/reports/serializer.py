"""Serializers for reports."""

import re
from datetime import datetime

from django.db import transaction
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DictField,
    ListField,
    ModelSerializer,
    Serializer,
    UUIDField,
    ValidationError,
)

from api.models import (
    InspectGroup,
    InspectResult,
    RawFact,
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


class ReportUploadSerializer(ModelSerializer):
    """Serializer for uploaded details reports."""

    report_type = ChoiceField(choices=["details"])
    report_platform_id = UUIDField()
    sources = SourceSerializer(many=True)

    class Meta:
        """Meta class for ReportUploadSerializer."""

        model = Report
        fields = ["report_platform_id", "report_type", "sources"]

    def validate_sources(self, value):
        """Validate sources."""
        if len(value) == 0:
            raise ValidationError("minimum length required for 'sources' is 1.")
        return value

    def update(self, *args, **kwargs):
        """Disable update method for this serializer."""
        # there's no way to 'update' a report
        raise NotImplementedError

    @transaction.atomic
    def create(self, validated_data):
        """Create a report filled with raw data and a fingerprint-type ScanJob."""
        # ignore other fields as they aren't part of Report model
        data = {"report_platform_id": validated_data["report_platform_id"]}
        report = super().create(data)
        # create a scan job and required scan tasks for a "upload" job
        scan_job = ScanJob.objects.create(
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            report=report,
            status=ScanTask.CREATED,
            start_time=datetime.now(),
        )
        # we don't have an actual inspection phase here, this task is only required
        # to tie RawFacts to the ScanJob and Report
        inspect_task = ScanTask.objects.create(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            status=ScanTask.COMPLETED,
            sequence_number=1,
        )
        ScanTask.objects.create(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            status=ScanTask.PENDING,
            sequence_number=2,
        )
        # finally, create all sources related objects
        inspect_group_list = []
        inspect_result_list = []
        raw_fact_list = []
        for source_dict in validated_data["sources"]:
            inspect_group = InspectGroup(
                source_type=source_dict["source_type"],
                source_name=source_dict["source_name"],
                server_id=source_dict["server_id"],
                server_version=source_dict["report_version"],
            )
            inspect_group_list.append(inspect_group)
            for fact_dict in source_dict["facts"]:
                inspect_result = InspectResult(inspect_group=inspect_group)
                inspect_result_list.append(inspect_result)
                raw_fact_list.extend(
                    RawFact(name=k, value=v, inspect_result=inspect_result)
                    for k, v in fact_dict.items()
                )
        InspectGroup.objects.bulk_create(inspect_group_list)
        InspectResult.objects.bulk_create(inspect_result_list)
        RawFact.objects.bulk_create(raw_fact_list)
        inspect_task.inspect_groups.set(inspect_group_list)
        return report
