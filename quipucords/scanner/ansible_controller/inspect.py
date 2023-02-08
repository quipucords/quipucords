from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction

from api.models import RawFact, ScanTask, SystemInspectionResult
from scanner.ansible_controller.task import AnsibleControllerTaskRunner
from scanner.exceptions import ScanFailureError


class InspectTaskRunner(AnsibleControllerTaskRunner):

    TARGET_HOST_FIELDS = [
        "name",
        "id",
        "created",
        "modified",
        "last_job",
        "inventory",
    ]

    def execute_task(self, manager_interrupt):
        self._check_prerequisites()
        client = self.get_client(self.scan_task)
        results = {"ansible_controller_host": self.system_name}
        results["hosts"] = self.get_hosts(client)
        # for now lets assume success
        inspection_status = SystemInspectionResult.SUCCESS
        self.save_results(inspection_status, results)

        if self.scan_task.systems_scanned:
            return self.success_message, ScanTask.COMPLETED
        return self.failure_message, ScanTask.FAILED

    def get_hosts(self, client):
        response = client.get("/api/v2/hosts/")
        if not response.ok:
            raise NotImplementedError()

        # skipping pagination info atm
        hosts = []
        for host in response.json()["results"]:
            parsed_host = {field: host.get(field) for field in self.TARGET_HOST_FIELDS}
            hosts.append(parsed_host)
        return hosts

    @transaction.atomic
    def save_results(self, inspection_status, facts_dict: dict):
        system = self._persist_facts(inspection_status, facts_dict)
        increment_kwargs = self._get_increment_kwargs(system.status)
        self.scan_task.increment_stats(self.system_name, **increment_kwargs)

    def _persist_facts(
        self, inspection_status, facts_dict: dict
    ) -> SystemInspectionResult:
        sys_result = SystemInspectionResult(
            name=self.system_name,
            status=inspection_status,
            source=self.scan_task.source,
            task_inspection_result=self.scan_task.inspection_result,
        )
        sys_result.save()
        raw_facts = self._facts_dict_as_raw_facts(sys_result, **facts_dict)
        RawFact.objects.bulk_create(raw_facts)
        return sys_result

    def _facts_dict_as_raw_facts(
        self, inspection_result: SystemInspectionResult, **facts_dict
    ) -> list[RawFact]:
        raw_facts = []
        for fact_name, fact_value in facts_dict.items():
            raw_facts.append(
                RawFact(
                    name=fact_name,
                    value=json.dumps(fact_value, default=str),
                    system_inspection_result=inspection_result,
                )
            )
        return raw_facts

    def _check_prerequisites(self):
        connect_scan_task = self.scan_task.prerequisites.first()
        if connect_scan_task.status != ScanTask.COMPLETED:
            raise ScanFailureError("Prerequisite scan have failed.")

    def _get_increment_kwargs(self, inspection_status):
        return {
            SystemInspectionResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "INSPECTED",
            },
            SystemInspectionResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
        }[inspection_status]
