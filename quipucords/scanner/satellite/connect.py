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
"""ScanTask used for satellite connection task."""
import socket

from requests import exceptions

from api.models import ScanTask
from scanner.satellite import utils
from scanner.satellite.api import SatelliteAuthException, SatelliteException
from scanner.satellite.factory import create
from scanner.task import ScanTaskRunner


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available systems.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.source = scan_task.source

    # pylint: disable=too-many-return-statements
    def run(self, manager_interrupt):
        """Scan Satellite for system connection data."""
        super_message, super_status = super().run(manager_interrupt)
        if super_status != ScanTask.COMPLETED:
            return super_message, super_status

        try:
            status_code, api_version, satellite_version = utils.status(self.scan_task)
            if status_code is None:
                error_message = "Unknown satellite version is not " "supported. "
                error_message += "Connect scan failed for source %s." % (
                    self.source.name
                )
                return error_message, ScanTask.FAILED
            if status_code == 200:
                api = create(
                    satellite_version, api_version, self.scan_job, self.scan_task
                )
                if not api:
                    error_message = (
                        "Satellite version %s with "
                        "api version %s is not supported.\n"
                        % (satellite_version, api_version)
                    )
                    error_message += "Connect scan failed for %s. " % self.source.name
                    return error_message, ScanTask.FAILED
                api.host_count()
                api.hosts()
            else:
                error_message = "Connect scan failed for source %s." % self.source.name
                return error_message, ScanTask.FAILED
        except SatelliteAuthException as auth_error:
            error_message = "Satellite auth error encountered: %s. " % auth_error
            error_message += "Connect scan failed for source %s." % self.source.name
            return error_message, ScanTask.FAILED
        except SatelliteException as sat_error:
            error_message = "Satellite unknown error encountered: %s. " % sat_error
            error_message += "Connect scan failed for source %s." % self.source.name
            return error_message, ScanTask.FAILED
        except exceptions.ConnectionError as conn_error:
            error_message = "Satellite connect error encountered: %s. " % conn_error
            error_message += "Connect scan failed for source %s." % self.source.name
            return error_message, ScanTask.FAILED
        except TimeoutError as timeout_error:
            error_message = "Satellite timeout error encountered: %s. " % timeout_error
            error_message += "Connect scan failed for source %s." % self.source.name
            return error_message, ScanTask.FAILED
        except socket.gaierror as socket_error:
            error_message = "Satellite gaierror error encountered: %s. " % socket_error
            error_message += "Connect scan failed for source %s." % self.source.name
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED
