"""Defines the models used with the API application.

These models are used in the REST definitions
"""

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.common.util import RawFactEncoder
from api.source.model import Source
from constants import DataSources


class InspectGroup(models.Model):
    """
    Model representing a collection of results and their common metadata.

    InspectGroup takes a snapshot of server and source information
    at the time the scan is run. This is required because:
    1. Reports require this information.
    2. source_type will ALWAYS be required for internal logic, and there are use cases
       where a ScanJob will not have Sources.
    3. New scans might have all this information modified - without taking a snapshot at
       during a scan would lead to older reports being inaccurate.
    4. Imported/Merged results won't point to a Source (and would be overkill to create
       a source instance only for source_type/name).
    """

    source_type = models.CharField(
        max_length=12, choices=DataSources.choices, null=False
    )
    source_name = models.CharField(max_length=64)
    server_id = models.CharField(max_length=36, null=False)
    server_version = models.CharField(max_length=64, null=False)

    tasks = models.ManyToManyField("ScanTask", related_name="inspect_groups")
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)


class InspectResult(models.Model):
    """A model for captured system data."""

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
    inspect_group = models.ForeignKey(
        InspectGroup,
        on_delete=models.CASCADE,
        null=False,
        related_name="inspect_results",
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SYS_INSPECT_RESULTS_MSG)


class RawFact(models.Model):
    """A model of a raw fact."""

    name = models.CharField(max_length=1024)
    value = models.JSONField(null=True, encoder=RawFactEncoder)
    inspect_result = models.ForeignKey(
        InspectResult, on_delete=models.CASCADE, related_name="facts"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_RAW_FACT_MSG)
