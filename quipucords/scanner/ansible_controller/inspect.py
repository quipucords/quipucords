from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction

from api.models import RawFact, ScanTask, SystemInspectionResult
from scanner.ansible_controller.task import AnsibleControllerTaskRunner
from scanner.exceptions import ScanFailureError


class InspectTaskRunner(AnsibleControllerTaskRunner):

    HOST_FIELDS = [
        "name",
        "id",
        "created",
        "modified",
        "last_job",
    ]
    JOB_FIELDS = [
        "id",
        "name",
        "status",
    ]

    def execute_task(self, manager_interrupt):
        self._check_prerequisites()
        client = self.get_client(self.scan_task)
        results = {"ansible_controller_host": self.system_name}
        results["hosts"] = self.get_hosts(client)
        results["jobs"] = self.get_jobs(client)
        results["comparison"] = self.compare_hosts(results)
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
            parsed_host = {field: host.get(field) for field in self.HOST_FIELDS}
            hosts.append(parsed_host)
        return hosts

    def get_jobs(self, client):
        jobs_response = client.get("/api/v2/jobs/")
        if not jobs_response.ok:
            raise NotImplementedError()
        job_ids = []
        unique_hosts = set()
        # ignoring pagination
        for job in jobs_response.json()["results"]:
            job_ids.append(job["id"])
            job_events_uri = job["related"]["job_events"]
            unique_hosts |= self.get_hosts_from_job_events(client, job_events_uri)
        return {"ids": job_ids, "unique_hosts": unique_hosts}

    def get_hosts_from_job_events(self, client, job_events_uri):
        response = client.get(job_events_uri)
        if not response.ok:
            raise NotImplementedError()
            # ignoring pagination once again
        events_data = response.json()
        unique_hosts = set()
        for event in events_data["results"]:
            unique_hosts.add(event["host_name"])
        # ignore garbage hosts
        unique_hosts -= {"", None}
        return unique_hosts

    def compare_hosts(self, data: dict):
        hosts_in_inventory = {host["name"] for host in data["hosts"]}
        hosts_in_jobs = data["jobs"]["unique_hosts"]
        hosts_not_in_inventory = hosts_in_jobs - hosts_in_inventory
        return {
            "hosts_in_inventory": hosts_in_inventory,
            "hosts_only_in_jobs": hosts_not_in_inventory,
            "number_of_hosts_in_inventory": len(hosts_in_inventory),
            "number_of_hosts_only_in_jobs": len(hosts_not_in_inventory),
        }

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
        def json_encoder(data):
            if isinstance(data, set):
                return sorted(data)
            else:
                return str(data)

        raw_facts = []
        for fact_name, fact_value in facts_dict.items():
            raw_facts.append(
                RawFact(
                    name=fact_name,
                    value=json.dumps(fact_value, default=json_encoder),
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
