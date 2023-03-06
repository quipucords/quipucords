"""Module for ScanTaskQuerySet."""

from django.db.models import F, JSONField, QuerySet
from django.db.models.functions import Cast


class ScanTaskQuerySet(QuerySet):
    """Specialized QuerySet for ScanTask model."""

    def raw_facts(self):
        """Gather RawFacts from SystemInspectionResult related to ScanTask."""
        systems_lookup = "inspection_result__systems"
        return (
            self.annotate(
                system_id=F(f"{systems_lookup}__id"),
                fact_name=F(f"{systems_lookup}__facts__name"),
                fact_value=Cast(F(f"{systems_lookup}__facts__value"), JSONField()),
            )
            .exclude(system_id=None)  # this is an artifact and should be removed
            .values_list(
                "system_id",
                "fact_name",
                "fact_value",
                named=True,
            )
            .order_by()
        )

    def raw_facts_per_system(self) -> dict:
        """Reformat raw_facts as a nested dict of facts per system."""
        facts_per_system = {}
        for system_id, fact_name, fact_value in self.all():
            try:
                facts_per_system[system_id][fact_name] = fact_value
            except KeyError:
                facts_per_system[system_id] = {fact_name: fact_value}
        return facts_per_system
