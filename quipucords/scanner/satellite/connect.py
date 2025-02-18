"""ScanTask used for satellite connection task."""
# TODO Remove this module.

import warnings

from api.scantask.model import ScanTask
from scanner.satellite.runner import SatelliteTaskRunner


class ConnectTaskRunner(SatelliteTaskRunner):
    """
    ConnectTaskRunner legacy interface does nothing for Satellite sources.

    TODO Remove this class when all source types stop using connect tasks.
    """

    def execute_task(self):
        """Scan Satellite for system connection data."""
        warnings.warn(
            "ConnectTaskRunner.execute_task does nothing.", DeprecationWarning
        )

        return None, ScanTask.COMPLETED

    def handle_api_calls(self, api):
        """Handle api calls for connetion phase."""
        warnings.warn(
            "ConnectTaskRunner.handle_api_calls does nothing.", DeprecationWarning
        )
