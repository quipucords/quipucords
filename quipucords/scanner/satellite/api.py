"""Satellite API Interface."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from functools import cached_property

import celery
from django.db import transaction

from api.inspectresult.model import InspectGroup
from api.models import (
    InspectResult,
    RawFact,
    Scan,
    SystemConnectionResult,
)
from api.status.misc import get_server_id
from quipucords.environment import server_version
from scanner.satellite import utils
from scanner.satellite.exceptions import SatelliteError

logger = logging.getLogger(__name__)


class SatelliteInterface(ABC):
    """Generic interface for dealing with Satellite."""

    def __init__(self, scan_job, scan_task):
        """Set context for interface."""
        self.scan_job = scan_job
        if scan_job.options is None:
            self.max_concurrency = Scan.DEFAULT_MAX_CONCURRENCY
        else:
            self.max_concurrency = scan_job.options.get(Scan.MAX_CONCURRENCY)

        self.inspect_scan_task = scan_task
        self.source = scan_task.source

    @transaction.atomic
    def record_conn_result(self, name, credential):
        """Record a new result.

        :param name: The host name
        :param credential: The authentication credential
        """
        SystemConnectionResult.objects.create(
            name=name,
            source=self.source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=self.inspect_scan_task.connection_result,
        )

    @cached_property
    def _inspect_group(self):
        inspect_group = InspectGroup.objects.create(
            source_type=self.inspect_scan_task.source.source_type,
            source_name=self.inspect_scan_task.source.name,
            server_id=get_server_id(),
            server_version=server_version(),
            source=self.inspect_scan_task.source,
        )
        inspect_group.tasks.add(self.inspect_scan_task)
        return inspect_group

    @transaction.atomic
    def record_inspect_result(self, name, facts, status=InspectResult.SUCCESS):
        """Record a new result.

        :param name: The host name
        :param facts: The dictionary of facts
        :param status: The status of the inspection
        """
        sys_result = InspectResult.objects.create(
            name=name, status=status, inspect_group=self._inspect_group
        )
        if status == InspectResult.SUCCESS:
            for key, val in facts.items():
                if val is not None:
                    stored_fact = RawFact(
                        name=key, value=val, inspect_result=sys_result
                    )
                    stored_fact.save()

        if status == InspectResult.SUCCESS:
            self.inspect_scan_task.increment_stats(name, increment_sys_scanned=True)
        elif status == InspectResult.UNREACHABLE:
            self.inspect_scan_task.increment_stats(name, increment_sys_unreachable=True)
        else:
            self.inspect_scan_task.increment_stats(name, increment_sys_failed=True)

    def _prepare_host_request_options(self):
        if self.inspect_scan_task is None:
            raise SatelliteError("host_details cannot be called for a connection scan")
        host, port, user, password, proxy_url = utils.get_connect_data(
            self.inspect_scan_task
        )

        ssl_cert_verify = self.inspect_scan_task.source.ssl_cert_verify
        if ssl_cert_verify is None:
            ssl_cert_verify = True

        request_options = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "ssl_cert_verify": ssl_cert_verify,
            "proxy_url": proxy_url,
        }
        return request_options

    def _prepare_and_process_hosts(
        self,
        hosts: Iterable[dict],
        request_host_details: Callable,
        process_results: Callable,
    ):
        self._prepare_and_process_hosts_using_celery(
            hosts, request_host_details, process_results
        )

    def _prepare_and_process_hosts_using_celery(
        self,
        hosts: Iterable[dict],
        request_host_details: Callable,
        process_results: Callable,
    ):
        """Prepare and process hosts using Celery tasks.

        Calling this function may result in a large number of Celery tasks, 1:1 with the
        number of hosts known by the Satellite server, and will synchronously block
        until all those tasks complete. This behavior does not follow Celery best
        practices and should be revised in the future.

        :param hosts: iterable of host dicts
        :param request_host_details: API version-specific function to get host details,
            must also be a registered Celery task
        :param process_results: API version-specific function to process results
        """
        all_prepared_hosts = self.prepare_hosts(hosts)
        # At the time of implementation, we don't know if it's okay to create many
        # tasks (one per hosts) in a group like this. If this proves problematic, we
        # should consider replacing `group` with `chunks` and calculate a reasonable
        # size to limit parallel load. For example:
        #     chunk_size = ceil(len(all_prepared_hosts) / self.max_concurrency)
        #     request_host_details.chunks(all_prepared_hosts, chunk_size)().get()
        #     results = list(itertools.chain.from_iterable(results))
        # FIXME We SHOULD NOT use disable_sync_subtasks=False.
        # Calling `get` blocks the current process, and if you do this from within a
        # running task, Celery normally raises `RuntimeError(E_WOULDBLOCK)` to
        # discourage that behavior. Although unlikely in *this* case, calling `get`
        # from inside a task may lead to deadlocks if there are not available Celery
        # workers; the blocking task may never complete and return its result to the
        # blocked task's `get` call. Setting `disable_sync_subtasks=False` bypasses
        # this internal Celery check, allowing the `get` to execute despite the risk.
        # See this discussion for more details:
        # https://github.com/quipucords/quipucords/pull/2364#discussion_r1229832809
        results = (
            celery.group(
                request_host_details.s(**host_params)
                for host_params in all_prepared_hosts
            )
            .apply_async()
            .get(disable_sync_subtasks=False)
        )
        process_results(results=results)

    def _prepare_host_logging_options(self):
        return {
            "job_id": self.scan_job.id,
            "task_sequence_number": self.inspect_scan_task.sequence_number,
            "scan_type": self.inspect_scan_task.scan_type,
            "source_type": self.inspect_scan_task.source.source_type,
            "source_name": self.inspect_scan_task.source.name,
        }

    @abstractmethod
    def prepare_hosts(self, hosts: Iterable[dict]) -> Iterable[dict]:
        """Prepare each host with necessary information."""

    @abstractmethod
    def host_count(self):
        """Obtain the count of managed hosts."""

    @abstractmethod
    def hosts(self):
        """Obtain the managed hosts."""

    @abstractmethod
    def hosts_facts(self):
        """Obtain the managed hosts detail raw facts."""
