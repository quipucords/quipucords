"""Defines the models used with the API application.

These models are used in the REST definitions
"""

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.common.util import RawFactEncoder
from api.source.model import Source


class JobInspectionResult(models.Model):
    """The results of a inspection scan."""

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_JOB_INSPECT_RESULTS_MSG)


class TaskInspectionResult(models.Model):
    """The captured inspection results from a scan."""

    job_inspection_result = models.ForeignKey(
        JobInspectionResult, on_delete=models.CASCADE, related_name="task_results"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_TASK_INSPECT_RESULTS_MSG)


class InspectResult(models.Model):
    """A model the of captured system data."""

    SUCCESS = "success"
    FAILED = "failed"
    UNREACHABLE = "unreachable"
    CONN_STATUS_CHOICES = (
        (SUCCESS, SUCCESS),
        (FAILED, FAILED),
        (UNREACHABLE, UNREACHABLE),
    )

    name = models.CharField(max_length=1024)
    status = models.CharField(max_length=12, choices=CONN_STATUS_CHOICES)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    task_inspection_result = models.ForeignKey(
        TaskInspectionResult, on_delete=models.CASCADE, related_name="systems"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SYS_INSPECT_RESULTS_MSG)


class RawFact(models.Model):
    """A model of a raw fact."""

    name = models.CharField(max_length=1024)
    value = models.JSONField(null=True, encoder=RawFactEncoder)
    system_inspection_result = models.ForeignKey(
        InspectResult, on_delete=models.CASCADE, related_name="facts"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_RAW_FACT_MSG)
