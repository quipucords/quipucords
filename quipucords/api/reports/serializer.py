from rest_framework.serializers import (
    CharField,
    DateTimeField,
    ListField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    Serializer,
    ValidationError,
)

from api.models import ScanJob, ScanTask
from api.reports.model import Report
from api.source.serializer import InternalSourceSerializer

SCANJOB_QUERYSET = ScanJob.objects.filter(
    # scan_type=ScanTask.SCAN_TYPE_INSPECT,
    status=ScanTask.COMPLETED,
)


class CreateReportSerializer(Serializer):
    from_jobs = ListField(
        child=PrimaryKeyRelatedField(queryset=SCANJOB_QUERYSET),
        required=False,
    )
    from_reports = ListField(
        child=PrimaryKeyRelatedField(
            queryset=Report.objects.filter(scanjob__in=SCANJOB_QUERYSET)
        ),
        required=False,
    )

    def validate(self, attrs):
        if not attrs:
            raise ValidationError("Either from_jobs or from_reports is required.")
        return super().validate(attrs)


class ReportOverviewSerializer(ModelSerializer):
    status = CharField(source="scanjob.status", read_only=True)
    start_time = DateTimeField(source="scanjob.start_time", read_only=True)
    end_time = DateTimeField(source="scanjob.end_time", read_only=True)
    sources = InternalSourceSerializer(source="scanjob.sources", many=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "report_platform_id",
            "status",
            "start_time",
            "end_time",
            "sources",
        ]
