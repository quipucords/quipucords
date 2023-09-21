"""Models to capture system facts."""

import uuid

from django.db import models

from api.inspectresult.model import RawFactEncoder


class Report(models.Model):
    """A reported set of facts."""

    report_version = models.CharField(max_length=64, null=False)
    # unique identifier required by yupana/insights
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    # ---------------------------- legacy fields ----------------------------
    # legacy data that should be (re)moved when we transition to the paradigm
    # of "normalization phase"
    sources = models.JSONField(null=False, default=list, encoder=RawFactEncoder)
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="report", null=True
    )
    cached_csv = models.TextField(null=True)
