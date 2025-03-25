"""ScanTask used for vcenter connection task."""

import logging
import warnings

from api.models import ScanTask
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner vcenter connection capabilities."""

    def execute_task(self):
        """Scan vcenter and attempt connections."""
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )
        return None, ScanTask.COMPLETED
