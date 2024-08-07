"""ScanTaskRunner is a logical breakdown of work."""

from abc import ABCMeta, abstractmethod
from multiprocessing import Value
from typing import Tuple

from api.models import ScanJob, ScanTask
from scanner.exceptions import (
    ScanCancelError,
    ScanFailureError,
    ScanInterruptError,
    ScanPauseError,
)


class ScanTaskRunner(metaclass=ABCMeta):
    """ScanTaskRunner is a logical breakdown of work."""

    def __init__(self, scan_job: ScanJob, scan_task: ScanTask):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        """
        self.scan_job = scan_job
        self.scan_task = scan_task

    def run(self, manager_interrupt: Value = None):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scan_task should be updated with status COMPLETE/FAILED
        before returning.

        :param manager_interrupt: Optional shared memory Value which can inform
        a task of the need to shut down immediately
        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """
        try:
            # Make sure job is not cancelled or paused
            self.check_for_interrupt(manager_interrupt)
            # call the inner task executor (should be implemented in concrete classes)
            return self.execute_task(manager_interrupt)
        except ScanInterruptError as interrupt_exc:
            return self.handle_interrupt_exception(interrupt_exc, manager_interrupt)
        except ScanFailureError as failure_error:
            return failure_error.message, ScanTask.FAILED

    def check_for_interrupt(self, manager_interrupt: Value):
        """Check if task runner should stop.

        This method should preferably be called after long-running commands.

        :param manager_interrupt: Signal to indicate job is canceled
        """
        if not manager_interrupt:
            return
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            raise ScanCancelError()
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            raise ScanPauseError()

    def handle_interrupt_exception(
        self, interrupt_exception: ScanInterruptError, manager_interrupt: Value
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
        a task of the need to shut down immediately

        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """

    def log(self, message, *args, **kwargs):
        """Shortcut for scan_task.log_message method."""
        self.scan_task.log_message(message, *args, **kwargs)

    def __str__(self):
        """Convert to string."""
        data = {
            "scan_job": self.scan_job.id,
            "sequence_number": self.scan_task.sequence_number,
            "scan_task": self.scan_task,
        }
        return str(data)
