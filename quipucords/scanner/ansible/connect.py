"""Connect task runner."""

from logging import getLogger

from django.conf import settings
from django.db import transaction
from requests import ConnectionError as RequestConnError
from requests import RequestException

from api.models import ScanTask, SystemConnectionResult
from scanner.ansible.runner import AnsibleTaskRunner

logger = getLogger(__name__)


class ConnectTaskRunner(AnsibleTaskRunner):
    """Connection phase task runner for ansible scanner."""

    def execute_task(self, manager_interrupt):
        """
        Execute the task and save the results.

        :param manager_interrupt: interrupt that can pause/cancel the scan
        :returns: tuple of human readable message and ScanTask.STATUS_CHOICE
        """
        self._init_stats()
        conn_result = SystemConnectionResult.FAILED
        try:
            self.client.get(
                "/api/v2/me/",
                timeout=settings.QPC_CONNECT_TASK_TIMEOUT,
                raise_for_status=True,
            )
            conn_result = SystemConnectionResult.SUCCESS
        except RequestException as exception:
            logger.exception("Unable to connect to '%s'.", self.system_name)
            if isinstance(exception, RequestConnError):
                conn_result = SystemConnectionResult.UNREACHABLE
            else:
                conn_result = SystemConnectionResult.FAILED
        self._save_results(conn_result)
        if conn_result == SystemConnectionResult.SUCCESS:
            return self.success_message, ScanTask.COMPLETED
        return self.failure_message, ScanTask.FAILED

    def _init_stats(self):
        """
        Initialize AAP connection stats.

        This is called at the start of a scan to set the number of scan tasks.
        """
        self.scan_task.update_stats(
            "INITIAL AAP CONNECT STATS.",
            sys_count=1,
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    @transaction.atomic
    def _save_results(self, conn_result):
        """Save results of connection."""
        increment_kwargs = self._get_increment_kwargs(conn_result)
        source = self.scan_task.source
        credential = source.single_credential
        sys_result = SystemConnectionResult(
            name=self.system_name,
            source=source,
            credential=credential,
            status=conn_result,
            task_connection_result=self.scan_task.connection_result,
        )
        sys_result.save()
        self.scan_task.increment_stats("UPDATED AAP CONNECT STATS.", **increment_kwargs)

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
