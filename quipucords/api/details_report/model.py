"""Models to capture system facts."""

import uuid

from django.db import models

from api.common.common_report import REPORT_TYPE_CHOICES, REPORT_TYPE_DETAILS


class DetailsReport(models.Model):
    """A reported set of facts."""

    report_type = models.CharField(
        max_length=11, choices=REPORT_TYPE_CHOICES, default=REPORT_TYPE_DETAILS
    )
    report_version = models.CharField(max_length=64, null=False)
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    sources = models.JSONField(null=False, default=list)
    report_id = models.IntegerField(null=True)
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="details_report", null=True
    )
    cached_csv = models.TextField(null=True)
