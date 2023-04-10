"""Defines the models used with the API application.

These models are used in the REST definitions
"""
from datetime import datetime
from json import JSONEncoder

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.source.model import Source
from compat.pydantic import BaseModel


class JobInspectionResult(models.Model):
    """The results of a inspection scan."""

    def __str__(self):
        """Convert to string."""
        # pylint: disable=no-member
        return f"{{ id:{self.id}, task_results:{self.task_results} }}"

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_JOB_INSPECT_RESULTS_MSG)


class TaskInspectionResult(models.Model):
    """The captured inspection results from a scan."""

    job_inspection_result = models.ForeignKey(
        JobInspectionResult, on_delete=models.CASCADE, related_name="task_results"
    )

    def __str__(self):
        """Convert to string."""
        # pylint: disable=no-member
        return f"{{ id:{self.id}, systems:{self.systems} }}"

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_TASK_INSPECT_RESULTS_MSG)


class SystemInspectionResult(models.Model):
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

    def __str__(self):
        """Convert to string."""
        # pylint: disable=no-member
        return (
            "{"
            f" id:{self.id},"
            f" name:{self.name},"
            f" status:{self.status},"
            f" facts:{self.facts},"
            f" source:{self.source} "
            "}"
        )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SYS_INSPECT_RESULTS_MSG)


class RawFactEncoder(JSONEncoder):
    """Customize the JSONField Encoder for RawFact values."""

    def default(self, o):
        """Update the default Encoder to handle types beyond just the basic ones."""
        if isinstance(o, BaseModel):
            return o.dict()
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, set):
            return sorted(o)
        return super().default(o)


class RawFact(models.Model):
    """A model of a raw fact."""

    name = models.CharField(max_length=1024)
    value = models.JSONField(null=True, encoder=RawFactEncoder)
    system_inspection_result = models.ForeignKey(
        SystemInspectionResult, on_delete=models.CASCADE, related_name="facts"
    )

    def __str__(self):
        """Convert to string."""
        # pylint: disable=no-member
        return f"{{ id:{self.id}, name:{self.name}, value:{self.value} }}"

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_RAW_FACT_MSG)
