"""Connect task runner."""

import logging

from django.conf import settings
from django.db import transaction

from api.models import ScanTask, SystemConnectionResult
from scanner.openshift.entities import OCPError
from scanner.openshift.runner import OpenShiftTaskRunner


class ConnectTaskRunner(OpenShiftTaskRunner):
    """Connect Task for OCP Scans."""

    SUCCESS_MESSAGE = "Connected to OpenShift host."
    FAILURE_MESSAGE = "Unable to connect to OpenShift host."

    def execute_task(self):
        """Scan OpenShift for system connection data."""
        self._init_stats()
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
        return self.FAILURE_MESSAGE, ScanTask.FAILED

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

    def _init_stats(self):
        self.scan_task.update_stats(
            "INITIAL OCP CONNECT STATS.",
            sys_count=1,
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    @transaction.atomic
    def _save_results(self, conn_result):
        increment_kwargs = self._get_increment_kwargs(conn_result)
        source = self.scan_task.source
        credential = source.single_credential
        sys_result = SystemConnectionResult(
            name=source.get_hosts()[0],
            source=source,
            credential=credential,
            status=conn_result,
            task_connection_result=self.scan_task.connection_result,
        )
        sys_result.save()
        self.scan_task.increment_stats("UPDATED OCP CONNECT STATS.", **increment_kwargs)

    def _get_increment_kwargs(self, conn_result):
        return {
            SystemConnectionResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "CONNECTED",
            },
            SystemConnectionResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
            SystemConnectionResult.UNREACHABLE: {
                "increment_sys_unreachable": True,
                "prefix": "UNREACHABLE",
            },
        }[conn_result]
