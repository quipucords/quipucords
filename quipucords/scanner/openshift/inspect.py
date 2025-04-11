"""OpenShift inspect task runner."""

import logging
from functools import cached_property

from django.conf import settings
from django.db import transaction

from api.connresult.model import SystemConnectionResult
from api.inspectresult.model import InspectGroup
from api.models import InspectResult, RawFact, ScanTask
from api.status.misc import get_server_id
from quipucords.environment import server_version
from scanner.openshift import metrics
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import OCPBaseEntity, OCPCluster, OCPError, OCPNode
from scanner.openshift.runner import OpenShiftTaskRunner


class InspectTaskRunner(OpenShiftTaskRunner):
    """OpenShift inspect task runner."""

    FAILURE_TO_CONNECT_MESSAGE = "Unable to connect to OpenShift host."
    SUCCESS_MESSAGE = "Inspected OpenShift host successfully."
    PARTIAL_SUCCESS_MESSAGE = (
        "Inspected some data from OpenShift host. Check details report for errors."
    )
    FAILURE_MESSAGE = "Unable to inspect OpenShift host."

    def execute_task(self):
        """Scan satellite manager and obtain host facts."""
        message, status = self.check_connection()
        if status != ScanTask.COMPLETED:
            return message, status

        message, status = self.inspect()
        return message, status

    def check_connection(self):
        """
        Check the connection before inspecting.

        This is redundant because we could just scan immediately and handle
        its failure as needed, but this exists due to legacy design decision
        that requires an existing list of connection results to be referenced
        later during the inspection. This could (should) be flattened into a
        single operation.

        TODO Remove this function when we remove connect scan tasks.
        """
        self._init_connection_stats()
        ocp_client = self.get_ocp_client(self.scan_task)
        try:
            ocp_client.can_connect(
                raise_exception=True,
                timeout_seconds=settings.QUIPUCORDS_CONNECT_TASK_TIMEOUT,
            )
            conn_result = SystemConnectionResult.SUCCESS
        except OCPError as error:
            conn_result = self._handle_ocp_error(error)

        self._save_results(conn_result)

        if conn_result == SystemConnectionResult.SUCCESS:
            return self.SUCCESS_MESSAGE, ScanTask.COMPLETED
        return self.FAILURE_TO_CONNECT_MESSAGE, ScanTask.FAILED

    def _init_connection_stats(self):
        self.scan_task.update_stats(
            "INITIAL OCP CONNECT STATS.",
            sys_count=1,
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    @cached_property
    def _inspect_group(self):
        inspect_group = InspectGroup.objects.create(
            source_type=self.scan_task.source.source_type,
            source_name=self.scan_task.source.name,
            server_id=get_server_id(),
            server_version=server_version(),
            source=self.scan_task.source,
        )
        inspect_group.tasks.add(self.scan_task)
        return inspect_group

    @transaction.atomic
    def _save_results(self, conn_result):
        increment_kwargs = self._get_increment_kwargs(conn_result)
        source = self.scan_task.source
        credential = source.single_credential
        SystemConnectionResult.objects.create(
            name=source.get_hosts()[0],
            source=source,
            credential=credential,
            status=conn_result,
            task_connection_result=self.scan_task.connection_result,
        )
        self.scan_task.increment_stats("UPDATED OCP CONNECT STATS.", **increment_kwargs)

    def inspect(self):
        """Perform the actual inspect operations and progressively save results."""
        ocp_client = self.get_ocp_client(self.scan_task)

        self.log("Retrieving essential cluster facts.")
        cluster = ocp_client.retrieve_cluster()

        self.log("Retrieving node facts.")
        nodes_list = ocp_client.retrieve_nodes(
            timeout_seconds=settings.QUIPUCORDS_INSPECT_TASK_TIMEOUT,
        )
        # cluster is considered a "system", hence the +1
        self._init_stats(len(nodes_list) + 1)
        for node in nodes_list:
            node.cluster_uuid = cluster.uuid
            self._save_node(node)

        self.log("Retrieving extra cluster facts.")
        extra_cluster_facts = self._extra_cluster_facts(ocp_client, cluster)
        self._save_cluster(cluster, extra_cluster_facts)

        self.log(f"Collected facts for {self.scan_task.systems_scanned} systems.")
        if self.scan_task.systems_failed:
            self.log(
                f"Failed collecting facts for {self.scan_task.systems_failed} systems."
            )

        if self.scan_task.systems_scanned and self.scan_task.systems_failed:
            return self.PARTIAL_SUCCESS_MESSAGE, ScanTask.COMPLETED
        if self.scan_task.systems_scanned:
            return self.SUCCESS_MESSAGE, ScanTask.COMPLETED
        return self.FAILURE_MESSAGE, ScanTask.FAILED

    def _extra_cluster_facts(self, ocp_client: OpenShiftApi, cluster):
        """Retrieve extra cluster facts."""
        collect_ocp_workloads_enabled = (
            settings.QUIPUCORDS_FEATURE_FLAGS.is_feature_active("OCP_WORKLOADS")
        )
        fact2method = (
            ("workloads", ocp_client.retrieve_workloads),
            ("operators", ocp_client.retrieve_operators),
            ("rhacm_metrics", ocp_client.retrieve_rhacm_metrics),
        )
        extra_facts = {}
        for fact_name, api_method in fact2method:
            try:
                if fact_name == "workloads" and not collect_ocp_workloads_enabled:
                    continue
                extra_facts[fact_name] = api_method(
                    timeout_seconds=settings.QUIPUCORDS_INSPECT_TASK_TIMEOUT
                )
            except OCPError as err:
                cluster.errors[fact_name] = err

        # Let's add the cluster metrics facts
        for fact_name, metric in metrics.OCP_PROMETHEUS_METRICS.items():
            try:
                extra_facts[fact_name] = metrics.retrieve_cluster_metrics(
                    ocp_client, metric
                )
            except OCPError as err:
                cluster.errors[fact_name] = err

        return extra_facts

    def _init_stats(self, number_of_systems):
        return self.scan_task.update_stats(
            "INITIAL OCP INSPECT STATS.",
            sys_count=number_of_systems,
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    def _handle_ocp_error(self, error: OCPError):
        if error.status == 401:  # noqa: PLR2004
            self.log(
                "Unable to Login to OpenShift host with credentials provided.",
                log_level=logging.ERROR,
            )
            return SystemConnectionResult.FAILED
        if error.status == -1:
            self.log(
                "Unable to login to OpenShift host. Check system logs.",
                log_level=logging.ERROR,
                exception=error,
            )
        else:
            self.log(
                f"Unable to reach OpenShift host. Got error {error}.",
                log_level=logging.ERROR,
            )
        return SystemConnectionResult.UNREACHABLE

    @transaction.atomic
    def _save_cluster(self, cluster: OCPCluster, cluster_facts):
        system_result = self._persist_cluster_facts(cluster, cluster_facts)
        increment_kwargs = self._get_increment_kwargs(system_result.status)
        self.scan_task.increment_stats(cluster.name, **increment_kwargs)

    @transaction.atomic
    def _save_node(self, node: OCPNode):
        system_result = self._persist_facts(node)
        increment_kwargs = self._get_increment_kwargs(system_result.status)
        self.scan_task.increment_stats(node.name, **increment_kwargs)

    def _persist_cluster_facts(self, cluster, other_facts):
        inspection_status = self._infer_inspection_status(cluster)
        system_result = InspectResult.objects.create(
            name=cluster.name,
            status=inspection_status,
            inspect_group=self._inspect_group,
        )
        raw_fact = self._entity_as_raw_fact(cluster, system_result)
        raw_fact.save()
        other_raw_facts = self._entities_as_raw_facts(system_result, other_facts)
        RawFact.objects.bulk_create(
            other_raw_facts, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        return system_result

    def _persist_facts(self, node: OCPNode) -> InspectResult:
        inspection_status = self._infer_inspection_status(node)
        sys_result = InspectResult.objects.create(
            name=node.name,
            status=inspection_status,
            inspect_group=self._inspect_group,
        )
        raw_fact = self._entity_as_raw_fact(node, sys_result)
        raw_fact.save()
        return sys_result

    def _entity_as_raw_fact(
        self, entity: OCPBaseEntity, inspection_result: InspectResult
    ) -> RawFact:
        return RawFact(
            name=entity.kind,
            value=entity,
            inspect_result=inspection_result,
        )

    def _entities_as_raw_facts(
        self, inspection_result: InspectResult, entities: dict
    ) -> list[RawFact]:
        raw_fact_list = []
        for collection_name, entity in entities.items():
            raw_fact = RawFact(
                name=collection_name,
                value=entity,
                inspect_result=inspection_result,
            )
            raw_fact_list.append(raw_fact)

        return raw_fact_list

    def _infer_inspection_status(self, entity):
        if entity.errors:
            return InspectResult.FAILED
        return InspectResult.SUCCESS

    def _get_increment_kwargs(self, inspection_status):
        # TODO FIXME Why sometimes InspectResult vs SystemConnectionResult?
        # These are used inconsistently throughout the code, not just here.
        # They hide the problem by coincidentally providing the same attributes.
        return {
            InspectResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "INSPECTED",
            },
            InspectResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
            SystemConnectionResult.UNREACHABLE: {
                "increment_sys_unreachable": True,
                "prefix": "UNREACHABLE",
            },
        }[inspection_status]
