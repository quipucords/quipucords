"""Satellite API Interface."""
import logging
from collections.abc import Callable, Iterable
from multiprocessing import Pool, Value

from django.db import transaction
from more_itertools import chunked

from api.models import (
    RawFact,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
    SystemInspectionResult,
)
from api.scanjob.model import ScanJob
from scanner.exceptions import ScanCancelException, ScanPauseException
from scanner.satellite import utils

logger = logging.getLogger(__name__)

SATELLITE_VERSION_5 = "5"
SATELLITE_VERSION_6 = "6"


class SatelliteAuthException(Exception):
    """Exception for Satellite Authentication interaction."""


class SatelliteException(Exception):
    """Exception for Satellite interaction."""


class SatelliteCancelException(ScanCancelException):
    """Exception for Satellite Cancel interrupt."""


class SatellitePauseException(ScanPauseException):
    """Exception for Satellite Pause interrupt."""


class SatelliteInterface:
    """Generic interface for dealing with Satellite."""

    def __init__(self, scan_job, scan_task):
        """Set context for interface."""
        self.scan_job = scan_job
        if scan_job.options is None:
            self.max_concurrency = ScanOptions.get_default_forks()
        else:
            self.max_concurrency = scan_job.options.max_concurrency

        if scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            self.connect_scan_task = scan_task
            self.inspect_scan_task = None
        else:
            self.connect_scan_task = scan_task.prerequisites.first()
            self.inspect_scan_task = scan_task
        self.source = scan_task.source

    @transaction.atomic
    def record_conn_result(self, name, credential):
        """Record a new result.

        :param name: The host name
        :param credential: The authentication credential
        """
        sys_result = SystemConnectionResult(
            name=name,
            source=self.source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=self.connect_scan_task.connection_result,
        )
        sys_result.save()

        self.connect_scan_task.increment_stats(name, increment_sys_scanned=True)

    @transaction.atomic
    def record_inspect_result(self, name, facts, status=SystemInspectionResult.SUCCESS):
        """Record a new result.

        :param name: The host name
        :param facts: The dictionary of facts
        :param status: The status of the inspection
        """
        sys_result = SystemInspectionResult(
            name=name,
            source=self.source,
            status=status,
            task_inspection_result=self.inspect_scan_task.inspection_result,
        )
        sys_result.save()

        if status == SystemInspectionResult.SUCCESS:
            for key, val in facts.items():
                if val is not None:
                    stored_fact = RawFact(
                        name=key, value=val, system_inspection_result=sys_result
                    )
                    stored_fact.save()

        if status == SystemInspectionResult.SUCCESS:
            self.inspect_scan_task.increment_stats(name, increment_sys_scanned=True)
        elif status == SystemInspectionResult.UNREACHABLE:
            self.inspect_scan_task.increment_stats(name, increment_sys_unreachable=True)
        else:
            self.inspect_scan_task.increment_stats(name, increment_sys_failed=True)

    def _prepare_host_request_options(self):
        if self.inspect_scan_task is None:
            raise SatelliteException(
                "host_details cannot be called for a connection scan"
            )
        host, port, user, password = utils.get_connect_data(self.inspect_scan_task)

        source_options = self.inspect_scan_task.source.options
        ssl_cert_verify = source_options.ssl_cert_verify if source_options else True

        request_options = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "ssl_cert_verify": ssl_cert_verify,
        }
        return request_options

    def _process_hosts_using_multiprocessing(
        self,
        hosts: Iterable[dict],
        request_host_details: Callable,
        process_results: Callable,
        manager_interrupt: Value,
    ):
        """Prepare and process hosts using multiprocessing.Pool.

        :param hosts: iterable of host dicts
        :param request_host_details: API version-specific function to get host details
        :param process_results: API version-specific function to process results
        :param manager_interrupt: shared multiprocessing value with possible interrupt
        """
        with Pool(processes=self.max_concurrency) as pool:
            for chunk in chunked(hosts, self.max_concurrency):
                if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
                    raise SatelliteCancelException()

                if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
                    raise SatellitePauseException()
                host_params = self.prepare_host(chunk)
                results = pool.starmap(request_host_details, host_params)
                process_results(results=results)

    def _prepare_host_logging_options(self):

        return {
            "job_id": self.scan_job.id,
            "task_sequence_number": self.inspect_scan_task.sequence_number,
            "scan_type": self.inspect_scan_task.scan_type,
            "source_type": self.inspect_scan_task.source.source_type,
            "source_name": self.inspect_scan_task.source.name,
        }

    def host_count(self):
        """Obtain the count of managed hosts."""

    def hosts(self):
        """Obtain the managed hosts."""

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
