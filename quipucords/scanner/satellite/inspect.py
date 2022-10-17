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
"""ScanTask used for satellite inspection task."""
from requests import exceptions

from api.models import ScanJob, ScanTask
from scanner.satellite import utils
from scanner.satellite.api import (
    SatelliteAuthException,
    SatelliteCancelException,
    SatelliteException,
    SatellitePauseException,
)
from scanner.satellite.factory import create
from scanner.task import ScanTaskRunner


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of a satellite managed system.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-return-statements,too-many-branches
    def execute_task(self, manager_interrupt):
        """Scan satellite manager and obtain host facts."""
        connect_scan_task = self.scan_task.prerequisites.first()
        if connect_scan_task.status != ScanTask.COMPLETED:
            error_message = "Prerequisites scan task %d failed." % (
                connect_scan_task.sequence_number
            )
            return error_message, ScanTask.FAILED
        source = self.scan_task.source
        try:
            status_code, api_version, satellite_version = utils.status(self.scan_task)
            if status_code is None:
                error_message = "Unknown satellite version is not " "supported. "
                error_message += "Inspect scan failed for source %s." % (source.name)
                return error_message, ScanTask.FAILED
            if status_code == 200:
                api = create(
                    satellite_version, api_version, self.scan_job, self.scan_task
                )
                if not api:
                    error_message = (
                        "Satellite version %s with "
                        "api version %s is not supported. "
                        % (satellite_version, api_version)
                    )
                    error_message += "Inspect scan failed for source %s." % (
                        source.name
                    )
                    return error_message, ScanTask.FAILED
                api.hosts_facts(manager_interrupt)
            else:
                error_message = "Inspect scan failed for source %s." % source.name
                return error_message, ScanTask.FAILED
        except SatelliteAuthException as auth_error:
            error_message = "Satellite auth error encountered: %s. " % auth_error
            error_message += "Inspect scan failed for source %s." % source.name
            return error_message, ScanTask.FAILED
        except SatelliteException as sat_error:
            error_message = "Satellite unknown error encountered: %s. " % sat_error
            error_message += "Inspect scan failed for source %s." % source.name
            return error_message, ScanTask.FAILED
        except exceptions.ConnectionError as conn_error:
            error_message = "Satellite connection error encountered: %s. " % conn_error
            error_message += "Inspect scan failed for %s." % source.name
            return error_message, ScanTask.FAILED
        except TimeoutError as timeout_error:
            error_message = "Satellite timeout error encountered: %s. " % timeout_error
            error_message += "Inspect scan failed for %s." % source.name
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED
