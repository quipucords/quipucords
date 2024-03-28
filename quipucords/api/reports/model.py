"""Models to capture system facts."""

import uuid
from functools import cached_property

from django.db import models

from api.inspectresult.model import ResultSet


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
        # result_sets = (
        #     ResultSet.objects.filter(tasks__job__report_id=self.id)
        #     .prefetch_related("inspect_results")
        #     .prefetch_related("inspect_results__facts")
        #     .order_by("id")
        #     .all()
        # )
        # source_list = []
        # for result_set in result_sets:
        #     source_dict = {
        #         "server_id": result_set.server_id,
        #         "report_version": result_set.server_version,
        #         "source_name": result_set.source_name,
        #         "source_type": result_set.source_type,
        #         "facts": [],
        #     }
        #     for result in result_set.inspect_results.all():
        #         facts = {fact.name: fact.value for fact in result.facts.all()}
        #         source_dict["facts"].append(facts)
        #     source_list.append(source_dict)
        # return source_list
        # =====================================================
        # result_set = (
        #     ResultSet.objects.with_raw_facts()
        #     .filter(tasks__job__report_id=self.id)
        # )
        # return [
        #     {
        #         "server_id": result_set.server_id,
        #         "report_version": result_set.server_version,
        #         "source_name": result_set.source_name,
        #         "source_type": result_set.source_type,
        #         "facts": result_set.facts,
        #     }
        #     for result_set in result_set
        # ]
        # =====================================================
        return (
            ResultSet.objects.with_raw_facts()
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
