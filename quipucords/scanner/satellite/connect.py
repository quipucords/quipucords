"""ScanTask used for satellite connection task."""


from scanner.satellite.runner import SatelliteTaskRunner


class ConnectTaskRunner(SatelliteTaskRunner):
    """ConnectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available systems.
    """

    def handle_api_calls(self, api, manager_interrupt):
        """Handle api calls for connetion phase."""
        api.host_count()
        api.hosts()
