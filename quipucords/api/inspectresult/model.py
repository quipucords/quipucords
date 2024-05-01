"""Defines the models used with the API application.

These models are used in the REST definitions
"""

from django.db import connection, models
from django.db.models.expressions import RawSQL
from django.utils.translation import gettext as _

from api import messages
from api.common.models import BaseModel
from api.common.util import RawFactEncoder
from api.source.model import Source
from constants import DataSources

RAW_QUERY_POSTGRES = """
with raw_agg(ir_id, inspect_group_id, raw_facts) as (
    select
        ir.id,
        ir.inspect_group_id,
        json_object_agg(raw.name, raw.value) as raw_facts
    from
        api_inspectresult ir
    inner join
        api_rawfact raw on ir.id = raw.inspect_result_id
    group by
        ir.id
)
select
    json_agg(raw_agg.raw_facts) as raw_fact_list
from raw_agg
where
    raw_agg.inspect_group_id=api_inspectgroup.id
group by
    raw_agg.inspect_group_id
"""


RAW_QUERY_SQLITE = """
with raw_agg(ir_id, inspect_group_id, raw_facts) as (
    select
        ir.id,
        ir.inspect_group_id,
        json_group_object(raw.name, json(raw.value)) as raw_facts
    from
        api_inspectresult ir
    inner join
        api_rawfact raw on ir.id = raw.inspect_result_id
    group by
        ir.id
)
select
    json_group_array(json(raw_agg.raw_facts)) as raw_fact_list
from raw_agg
where
    raw_agg.inspect_group_id=api_inspectgroup.id
group by
    raw_agg.inspect_group_id
"""


class InspectGroupQuerySet(models.QuerySet):
    """Custom QuerySet for InspectGroup model."""

    def with_raw_facts(self):
        """Annotate results with raw facts."""
        if connection.vendor == "postgresql":
            raw_sql = RAW_QUERY_POSTGRES
            raw_sql_kw = {}
        elif connection.vendor == "sqlite":
            raw_sql = RAW_QUERY_SQLITE
            raw_sql_kw = {"output_field": models.JSONField()}
        else:  # pragma: no cover
            raise NotImplementedError(
                f"with_raw_facts not implemented for {connection.vendor=}"
            )
        # Disabled S611 because no user input will influence this query and we
        # actually need RawSQL for performance reasons.
        return self.annotate(
            facts=RawSQL(raw_sql, params=(), **raw_sql_kw)  # noqa: S611
        )


class InspectGroup(BaseModel):
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

    objects = InspectGroupQuerySet.as_manager()


class InspectResult(BaseModel):
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


class RawFact(BaseModel):
    """A model of a raw fact."""

    name = models.CharField(max_length=1024)
    value = models.JSONField(null=True, encoder=RawFactEncoder)
    inspect_result = models.ForeignKey(
        InspectResult, on_delete=models.CASCADE, related_name="facts"
    )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_RAW_FACT_MSG)
