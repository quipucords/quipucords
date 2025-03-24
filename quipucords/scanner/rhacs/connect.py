"""Connect task runner."""

import warnings
from logging import getLogger

from api.models import ScanTask
from scanner.rhacs.runner import RHACSTaskRunner

logger = getLogger(__name__)


class ConnectTaskRunner(RHACSTaskRunner):
    """Connection phase task runner for RHACS scanner."""

    def execute_task(self):
        """
        Execute the task and save the results.

        :returns: tuple of human readable message and ScanTask.STATUS_CHOICE
        """
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )
        return None, ScanTask.COMPLETED
