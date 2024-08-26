"""ScanTaskRunner is a logical breakdown of work."""

from abc import ABCMeta, abstractmethod
from typing import Tuple

from api.models import ScanJob, ScanTask
from scanner.exceptions import (
    ScanFailureError,
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

    def run(self):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scan_task should be updated with status COMPLETE/FAILED
        before returning.

        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """
        try:
            # call the inner task executor (should be implemented in concrete classes)
            return self.execute_task()
        except ScanFailureError as failure_error:
            return failure_error.message, ScanTask.FAILED

    @abstractmethod
    def execute_task(self) -> Tuple[str, str]:
        """
        Actual logic for each implementation of ScanTaskRunner.

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
