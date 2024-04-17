"""Models to capture system facts."""

import uuid
from functools import cached_property

from django.db import models

from api.inspectresult.model import InspectGroup


class Report(models.Model):
    """A reported set of facts."""

    report_version = models.CharField(max_length=64, null=False)
    # report_platform_id is a unique identifier required by yupana/insights
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    # ---------------------------- legacy fields ----------------------------
    # legacy data that should be (re)moved when we transition to the paradigm
    # of "normalization phase"
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="report", null=True
    )
    cached_csv = models.TextField(null=True)

    @cached_property
    def sources(self):
        """Drop in replacement for the now defunct "sources" JSONField."""
        return (
            InspectGroup.objects.with_raw_facts()
            .filter(tasks__job__report_id=self.id)
            .annotate(report_version=models.F("server_version"))
            .values(
                "server_id",
                "report_version",
                "source_name",
                "source_type",
                "facts",
            )
        )
