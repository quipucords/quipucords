"""ScanTask used for network connection discovery."""

from __future__ import annotations

import logging
import warnings

from api.models import ScanTask
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def execute_task(self):
        """Scan network range and attempt connections."""
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )
        return None, ScanTask.COMPLETED
