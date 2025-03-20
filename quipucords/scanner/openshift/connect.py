"""Connect task runner."""

import warnings

from api.models import ScanTask
from scanner.openshift.runner import OpenShiftTaskRunner


class ConnectTaskRunner(OpenShiftTaskRunner):
    """Connect Task for OCP Scans."""

    def execute_task(self):
        """Scan OpenShift for system connection data."""
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )
        return None, ScanTask.COMPLETED
