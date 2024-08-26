"""Inspection phase for RHACS scanner."""

from __future__ import annotations

from logging import getLogger

from django.conf import settings
from django.db import transaction
from requests import RequestException

from api.inspectresult.model import InspectGroup
from api.models import InspectResult, RawFact, ScanTask
from api.status.misc import get_server_id
from quipucords.environment import server_version
from scanner.exceptions import ScanFailureError
from scanner.rhacs.runner import RHACSTaskRunner

logger = getLogger(__name__)


class InspectTaskRunner(RHACSTaskRunner):
    """Inspection phase task runner for RHACS scanner."""

    REQUEST_KWARGS = {
        "raise_for_status": True,
        "timeout": settings.QPC_INSPECT_TASK_TIMEOUT,
    }

    def execute_task(self):
        """
        Execute the task and save the results.

        :returns: tuple of human readable message and ScanTask.STATUS_CHOICE
        """
        self._check_prerequisites()

        results = {}
        inspection_status = InspectResult.SUCCESS
        collectable_facts = ("secured_units_current", "secured_units_max")
        for fact in collectable_facts:
            method = getattr(self, f"get_{fact}")
            try:
                results[fact] = method()
            except RequestException:
                logger.exception(
                    "Error collecting fact '%s' for RHACS host '%s'.",
                    fact,
                    self.system_name,
                )
                inspection_status = InspectResult.FAILED

        self.save_results(inspection_status, results)

        if self.scan_task.systems_scanned:
            return self.success_message, ScanTask.COMPLETED
        return self.failure_message, ScanTask.FAILED

    def _fetch_rhacs_metric(self, endpoint):
        """Fetch RHACS metrics data from a given endpoint."""
        response = self.client.get(endpoint)
        response.raise_for_status()
        return response.json()

    def get_secured_units_current(self):
        """Retrieve RHACS secured node/cpu units metrics."""
        secured_units_current = self._fetch_rhacs_metric(
            "/v1/administration/usage/secured-units/current"
        )
        return secured_units_current

    def get_secured_units_max(self):
        """Retrieve RHACS max secured node/cpu units metrics."""
        secured_units_max = self._fetch_rhacs_metric(
            "/v1/administration/usage/secured-units/max"
        )
        return secured_units_max

    @transaction.atomic
    def save_results(self, inspection_status, facts_dict: dict):
        """
        Save inspection results to the scan task.

        Stores the results of the inspection in the system and increments the statistics
        for the scan task.

        :param inspection_status: The status of the inspection
        :param facts_dict: Dictionary of facts to be saved to
        """
        system = self._persist_facts(inspection_status, facts_dict)
        increment_kwargs = self._get_increment_kwargs(system.status)
        self.scan_task.increment_stats(self.system_name, **increment_kwargs)

    def _persist_facts(self, inspection_status, facts_dict: dict) -> InspectResult:
        """
        Persist facts to database.

        :param inspection_status: status of the inspection
        :param facts_dict: dictionary of facts to persist
        """
        inspect_group = InspectGroup.objects.create(
            source_type=self.scan_task.source.source_type,
            source_name=self.scan_task.source.name,
            server_id=get_server_id(),
            server_version=server_version(),
            source=self.scan_task.source,
        )
        inspect_group.tasks.add(self.scan_task)
        sys_result = InspectResult.objects.create(
            name=self.system_name,
            status=inspection_status,
            inspect_group=inspect_group,
        )
        raw_facts = self._facts_dict_as_raw_facts(sys_result, **facts_dict)
        RawFact.objects.bulk_create(
            raw_facts, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        return sys_result

    def _facts_dict_as_raw_facts(
        self, inspection_result: InspectResult, **facts_dict
    ) -> list[RawFact]:
        """
        Convert a dictionary of facts to a list of RawFacts.

        :param inspection_result: The SystemInspectionResult that will be used to
         determine if facts are valid
        """
        raw_facts = []
        for fact_name, fact_value in facts_dict.items():
            raw_facts.append(
                RawFact(
                    name=fact_name,
                    value=fact_value,
                    inspect_result=inspection_result,
                )
            )
        return raw_facts

    def _check_prerequisites(self):
        """
        Check prerequisites of ScanTask are completed.

        Raises ScanFailureError if prerequisites are not met.
        """
        connect_scan_task = self.scan_task.prerequisites.first()
        if connect_scan_task.status != ScanTask.COMPLETED:
            raise ScanFailureError("Prerequisite scan have failed.")

    def _get_increment_kwargs(self, inspection_status):
        return {
            InspectResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "INSPECTED",
            },
            InspectResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
        }[inspection_status]
