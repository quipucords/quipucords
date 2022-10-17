#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTaskRunner is a logical breakdown of work."""

from abc import ABCMeta, abstractmethod
from multiprocessing import Value
from typing import Tuple

from api.models import ScanJob, ScanTask
from scanner.exceptions import ScanInterruptException


class ScanTaskRunner(metaclass=ABCMeta):
    """ScanTaskRunner is a logical breakdown of work."""

    def __init__(
        self, scan_job: ScanJob, scan_task: ScanTask, supports_partial_results=False
    ):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param supports_partial_results: Indicates if task supports
            partial results.
        """
        self.scan_job = scan_job
        self.scan_task = scan_task
        self.supports_partial_results = supports_partial_results

        if not supports_partial_results:
            self.scan_task.reset_stats()
            if self.scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
                self.scan_task.connection_result.systems.all().delete()
            elif self.scan_task.scan_type == ScanTask.SCAN_TYPE_INSPECT:
                self.scan_task.inspection_result.systems.all().delete()
            elif self.scan_task.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
                details_report = self.scan_task.details_report
                if details_report:
                    # remove results from previous interrupted scan
                    deployment_report = details_report.deployment_report

                    if deployment_report:
                        # remove partial results
                        self.scan_task.log_message(
                            "REMOVING PARTIAL RESULTS - deleting %d "
                            "fingerprints from previous scan"
                            % deployment_report.system_fingerprints.count()
                        )
                        deployment_report.system_fingerprints.all().delete()
                        deployment_report.save()
                        details_report.deployment_report = None
                        details_report.save()
                        deployment_report.delete()

    def run(self, manager_interrupt: Value):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scan_task should be updated with status COMPLETE/FAILED
        before returning.

        :param manager_interrupt: Shared memory Value which can inform
        a task of the need to shutdown immediately
        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """
        # Make sure job is not cancelled or paused
        message, task_status = self.check_for_interrupt(manager_interrupt)
        if task_status != ScanTask.RUNNING:
            return message, task_status
        try:
            # call the inner task executor (should be implemented in concrete classes)
            return self.execute_task(manager_interrupt)
        except ScanInterruptException as interrupt_exc:
            return self.handle_interrupt_exception(interrupt_exc, manager_interrupt)

    def check_for_interrupt(self, manager_interrupt: Value):
        """Check if task runner should stop.

        :param manager_interrupt: Signal to indicate job is canceled
        :return status, message indicating if shutdown should occur.
            ScanTask.RUNNING indicates process should continue
        """
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return "Scan canceled", ScanTask.CANCELED

        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return "Scan paused", ScanTask.PAUSED
        return "keep going", ScanTask.RUNNING

    def handle_interrupt_exception(
        self, interrupt_exception: ScanInterruptException, manager_interrupt: Value
    ):
        """Stop scan job when InterruptScanException is raised."""
        manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
        error_message = (
            f"Scan '{self.scan_task.scan_type}' "
            f"got signal to {interrupt_exception.STATUS} "
            f"for source='{self.scan_task.source}'."
        )
        return error_message, interrupt_exception.STATUS

    @abstractmethod
    def execute_task(self, manager_interrupt: Value) -> Tuple[str, str]:
        """
        Actual logic for each implementation of ScanTaskRunner.

        :param manager_interrupt: Shared memory Value which can inform
        a task of the need to shutdown immediately

        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """

    def __str__(self):
        """Convert to string."""
        data = {
            "scan_job": self.scan_job.id,
            "sequence_number": self.scan_task.sequence_number,
            "scan_task": self.scan_task,
        }
        return str(data)
