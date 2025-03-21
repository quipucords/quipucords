"""Connect task runner."""

import warnings
from logging import getLogger

from api.models import ScanTask
from scanner.ansible.runner import AnsibleTaskRunner

logger = getLogger(__name__)


class ConnectTaskRunner(AnsibleTaskRunner):
    """Connection phase task runner for ansible scanner."""

    def execute_task(self):
        """
        Execute the task and save the results.

        :returns: tuple of human readable message and ScanTask.STATUS_CHOICE
        """
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )
        return None, ScanTask.COMPLETED
