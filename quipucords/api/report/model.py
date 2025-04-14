"""Models to capture system facts."""

import uuid
import warnings
from functools import cached_property

from django.db import models

from api.common.common_report import create_report_version
from api.common.models import BaseModel


class Report(BaseModel):
    """A reported set of facts."""

    report_version = models.CharField(
        max_length=64, null=False, default=create_report_version
    )
    # report_platform_id is a unique identifier required by yupana/insights
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    inspect_groups = models.ManyToManyField("InspectGroup", related_name="reports")
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
