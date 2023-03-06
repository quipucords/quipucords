"""ScanTask used for satellite inspection task."""

from requests import exceptions

from api.models import ScanTask
from scanner.satellite.api import SatelliteAuthException, SatelliteException
from scanner.satellite.task import SatelliteTaskRunner


class InspectTaskRunner(SatelliteTaskRunner):
    """InspectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of a satellite managed system.
    """

    EXPECTED_EXCEPTIONS = (
        SatelliteAuthException,
        SatelliteException,
        exceptions.ConnectionError,
        TimeoutError,
    )

    def execute_task(self, manager_interrupt):
        """Scan satellite manager and obtain host facts."""
        conn_task = self.scan_task.prerequisites.first()
        if conn_task.status != ScanTask.COMPLETED:
            error_message = (
                f"Prerequisites scan task {conn_task.sequence_number} failed."
            )
            return error_message, ScanTask.FAILED
        return super().execute_task(manager_interrupt)

    def handle_api_calls(self, api, manager_interrupt):
        """Handle api calls for inspection phase."""
        api.hosts_facts(manager_interrupt)
