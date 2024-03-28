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
        inspect_groups = (
            InspectGroup.objects.filter(tasks__job__report_id=self.id)
            .prefetch_related("inspect_results")
            .prefetch_related("inspect_results__facts")
            .order_by("id")
            .all()
        )
        source_list = []
        for inspect_group in inspect_groups:
            source_dict = {
                "server_id": inspect_group.server_id,
                "report_version": inspect_group.server_version,
                "source_name": inspect_group.source_name,
                "source_type": inspect_group.source_type,
                "facts": [],
            }
            for result in inspect_group.inspect_results.all():
                facts = {fact.name: fact.value for fact in result.facts.all()}
                source_dict["facts"].append(facts)
            source_list.append(source_dict)
        return source_list
