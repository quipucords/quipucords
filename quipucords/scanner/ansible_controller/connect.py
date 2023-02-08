# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Connect task runner."""

from django.conf import settings
from django.db import transaction

from api.models import ScanTask, SystemConnectionResult
from scanner.ansible_controller.task import AnsibleControllerTaskRunner


class ConnectTaskRunner(AnsibleControllerTaskRunner):
    def execute_task(self, manager_interrupt):
        self._init_stats()
        client = self.get_client(self.scan_task)

        conn_result = SystemConnectionResult.FAILED
        response = client.get("/api/v2/me/", timeout=settings.QPC_CONNECT_TASK_TIMEOUT)
        if response.ok:
            conn_result = SystemConnectionResult.SUCCESS
        self._save_results(conn_result)

        if conn_result == SystemConnectionResult.SUCCESS:
            return self.success_message, ScanTask.COMPLETED
        return self.failure_message, ScanTask.FAILED

    def _init_stats(self):
        self.scan_task.update_stats(
            "INITIAL AAP CONNECT STATS.",
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
