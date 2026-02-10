"""Models to capture system facts."""

import uuid
import warnings
from functools import cached_property

from django.db import models

from api.common.common_report import create_report_version
from api.common.enumerators import ReportCannotDownloadReason
from api.common.models import BaseModel
from api.deployments_report.model import DeploymentsReport


class Report(BaseModel):
    """A reported set of facts."""

    LOCAL = "local"
    UPLOADED = "uploaded"
    MERGED = "merged"
    ORIGIN_CHOICES = (
        (LOCAL, LOCAL),
        (UPLOADED, UPLOADED),
        (MERGED, MERGED),
    )

    report_version = models.CharField(
        max_length=64, null=False, default=create_report_version
    )
    # report_platform_id is a unique identifier required by yupana/insights
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    inspect_groups = models.ManyToManyField("InspectGroup", related_name="reports")
    origin = models.CharField(
        choices=ORIGIN_CHOICES,
        default=LOCAL,
        null=False,
    )
    # ---------------------------- legacy fields ----------------------------
    # legacy data that should be (re)moved when we transition to the paradigm
    # of "normalization phase"
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="report", null=True
    )
    cached_csv = models.TextField(null=True)

    @cached_property
    def sources(self):
        """
        Drop in replacement for the now defunct "sources" JSONField.

        Returns a InspectGroupQuerySet.
        """
        warnings.warn(
            "Report.sources will be deprecated in the near future.",
            DeprecationWarning,
        )
        return (
            self.inspect_groups.with_raw_facts()
            .annotate(report_version=models.F("server_version"))
            .values(
                "server_id",
                "report_version",
                "source_name",
                "source_type",
                "facts",
            )
        )

    @cached_property
    def cannot_publish_reason(self):
        """Explanation why report can't be published to Lightspeed, or None."""
        from api.common.lightspeed import get_cannot_publish_reason

        return get_cannot_publish_reason(self)

    @property
    def can_publish(self) -> bool:
        """Whether report can be published to Lightspeed."""
        return self.cannot_publish_reason is None

    @cached_property
    def cannot_download_reason(self):
        """Explanation why report can't be downloaded, or None."""
        if not self.deployment_report:
            return ReportCannotDownloadReason.NO_DEPLOYMENT
        if self.deployment_report.status == DeploymentsReport.STATUS_PENDING:
            return ReportCannotDownloadReason.STATUS_PENDING
        if self.deployment_report.status == DeploymentsReport.STATUS_FAILED:
            return ReportCannotDownloadReason.STATUS_FAILED
        return None

    @property
    def can_download(self) -> bool:
        """Whether report can be downloaded."""
        return self.cannot_download_reason is None
