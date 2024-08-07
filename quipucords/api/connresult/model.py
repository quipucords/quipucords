"""Defines the models used with the API application.

These models are used in the REST definitions
"""

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.common.models import BaseModel
from api.credential.model import Credential
from api.source.model import Source


class JobConnectionResult(BaseModel):
    """The results of a connection scan."""

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_JOB_CONN_RESULTS_MSG)


class TaskConnectionResult(BaseModel):
    """The captured connection results from a scan."""

    job_connection_result = models.ForeignKey(
        JobConnectionResult, on_delete=models.CASCADE, related_name="task_results"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_TASK_CONN_RESULTS_MSG)


class SystemConnectionResult(BaseModel):
    """A key value pair of captured data."""

    SUCCESS = "success"
    FAILED = "failed"
    UNREACHABLE = "unreachable"
    CONN_STATUS_CHOICES = (
        (SUCCESS, SUCCESS),
        (FAILED, FAILED),
        (UNREACHABLE, UNREACHABLE),
    )

    name = models.TextField()
    credential = models.ForeignKey(Credential, on_delete=models.SET_NULL, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=12, choices=CONN_STATUS_CHOICES)
    task_connection_result = models.ForeignKey(
        TaskConnectionResult, on_delete=models.CASCADE, related_name="systems"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SYS_CONN_RESULTS_MSG)
