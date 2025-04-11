"""ScanTask used for satellite inspection task."""

from requests import exceptions

from scanner.satellite.exceptions import SatelliteAuthError, SatelliteError
from scanner.satellite.runner import SatelliteTaskRunner


class InspectTaskRunner(SatelliteTaskRunner):
    """InspectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of a satellite managed system.
    """

    EXPECTED_EXCEPTIONS = (
        SatelliteAuthError,
        SatelliteError,
        exceptions.ConnectionError,
        TimeoutError,
    )

    def handle_api_calls(self, api):
        """Handle api calls for inspection phase."""
        api.host_count()
        api.hosts()
        api.hosts_facts()
