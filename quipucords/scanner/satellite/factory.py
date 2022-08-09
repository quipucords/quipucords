#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

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
    if api_version == 2:
        return SatelliteSixV2(scan_job, scan_task)
    return None
