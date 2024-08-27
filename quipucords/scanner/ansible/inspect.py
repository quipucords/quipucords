"""inspection phase for ansible controller scanner."""

from __future__ import annotations

from logging import getLogger

from django.conf import settings
from django.db import transaction
from requests import RequestException

from api.models import InspectGroup, InspectResult, RawFact, Scan, ScanTask
from api.status.misc import get_server_id
from quipucords.environment import server_version
from scanner.ansible.runner import AnsibleTaskRunner
from scanner.exceptions import ScanFailureError

logger = getLogger(__name__)


class InspectTaskRunner(AnsibleTaskRunner):
    """Inspection phase task runner for ansible scanner."""

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
    REQUEST_KWARGS = {
        "raise_for_status": True,
        "timeout": settings.QUIPUCORDS_INSPECT_TASK_TIMEOUT,
    }

    def execute_task(self):
        """
        Execute the task and save the results.

        :returns: tuple of human readable message and ScanTask.STATUS_CHOICE
        """
        self._check_prerequisites()
        results = {}
        inspection_status = InspectResult.SUCCESS
        collectable_facts = ("instance_details", "hosts", "jobs")
        for fact in collectable_facts:
            method = getattr(self, f"get_{fact}")
            try:
                results[fact] = method()
            except RequestException:
                logger.exception(
                    "Error collecting fact '%s' for ansible host '%s'.",
                    fact,
                    self.system_name,
                )
                inspection_status = InspectResult.FAILED

        if inspection_status == InspectResult.SUCCESS:
            results["comparison"] = self.compare_hosts(results)
        self.save_results(inspection_status, results)

        if self.scan_task.systems_scanned:
            return self.success_message, ScanTask.COMPLETED
        return self.failure_message, ScanTask.FAILED

    @property
    def max_concurrency(self):
        """Return scan job max concurrency option."""
        try:
            return self.scan_task.job.options.get(Scan.MAX_CONCURRENCY)
        except AttributeError:
            return Scan.DEFAULT_MAX_CONCURRENCY

    def get_hosts(self) -> list[dict]:
        """Retrieve ansible managed hosts/nodes."""
        hosts_generator = self.client.get_paginated_results(
            "/api/v2/hosts/",
            max_concurrency=self.max_concurrency,
            **self.REQUEST_KWARGS,
        )
        hosts = []
        for host in hosts_generator:
            parsed_host = {field: host.get(field) for field in self.HOST_FIELDS}
            parsed_host["host_id"] = parsed_host.pop("id")
            hosts.append(parsed_host)
        return hosts

    def get_instance_details(self) -> dict:
        """
        Retrieve ansible managed hosts/nodes.

        :param client: AnsibleControllerApi to use for API calls
        :returns: A list of dicts containing information about each host in.
        """
        response = self.client.get("/api/v2/ping/", **self.REQUEST_KWARGS)
        data = response.json()
        # set "system_name" (aka connection host) for use on fingerprint phase
        data["system_name"] = data.get("active_node") or self.system_name
        return data

    def get_jobs(self) -> list[dict]:
        """
        Retrieve all job ids and unique hosts.

        :param client: AnsibleControllerApi to use for API calls
        :returns: a dictionary with job ids and unique hosts.
        """
        jobs_generator = self.client.get_paginated_results(
            "/api/v2/jobs/",
            max_concurrency=self.max_concurrency,
            **self.REQUEST_KWARGS,
        )
        job_ids = []
        unique_hosts = set()
        # ignoring pagination
        for job in jobs_generator:
            job_id = job["id"]
            job_ids.append(job_id)
            unique_hosts |= self.get_hosts_from_job_events(job_id)
        return {"job_ids": job_ids, "unique_hosts": unique_hosts}

    def get_hosts_from_job_events(self, job_id) -> set:
        """Get unique hosts found in job events."""
        events_generator = self.client.get_paginated_results(
            f"api/v2/jobs/{job_id}/job_events/?event=runner_on_start",
            **self.REQUEST_KWARGS,
        )
        unique_hosts = set()
        for event in events_generator:
            unique_hosts.add(event["host_name"])
        # ignore garbage hosts
        unique_hosts -= {"", None}
        return unique_hosts

    def compare_hosts(self, data: dict) -> dict:
        """Compare the hosts found in inventory and in jobs."""
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
