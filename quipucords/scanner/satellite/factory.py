"""Factory for Satellite Interface."""

from scanner.satellite.api import SATELLITE_VERSION_5
from scanner.satellite.five import SatelliteFive
from scanner.satellite.six import SatelliteSixV1, SatelliteSixV2


def create(satellite_version, api_version, scan_job, scan_task):
    """Create the appropriate SatelliteInterface."""
    if satellite_version is None:
        return None
    if satellite_version == SATELLITE_VERSION_5:
        return SatelliteFive(scan_job, scan_task)
    if api_version == 1:
        return SatelliteSixV1(scan_job, scan_task)
    if api_version == 2:  # noqa: PLR2004
        return SatelliteSixV2(scan_job, scan_task)
    return None
