#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for satellite inspection task."""
import logging
from requests import exceptions
from api.models import (ScanTask, SourceOptions,
                        ConnectionResult, InspectionResult)
from scanner.task import ScanTaskRunner
from scanner.satellite import utils
from scanner.satellite.api import SatelliteException
from scanner.satellite.factory import create

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner satellite connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of a satellite managed system.
    """

    def __init__(self, scan_job, scan_task, inspect_results):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        super().__init__(scan_job, scan_task)
        self.inspect_results = inspect_results
        self.source = scan_task.source
        self.connect_scan_task = None
        self.conn_result = None
        self.inspect_result = None

    # pylint: disable=too-many-return-statements
    def run(self):
        """Scan satellite manager and obtain host facts."""
        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            logger.error(
                'Prerequisites scan task with id %d failed.',
                self.connect_scan_task.id)
            return ScanTask.FAILED

        satellite_version = None
        options = self.source.options
        if options:
            satellite_version = options.satellite_version

        if (satellite_version is None or
                satellite_version == SourceOptions.SATELLITE_VERSION_5):
            logger.error('Satellite version %s is not yet supported.',
                         SourceOptions.SATELLITE_VERSION_5)
            logger.error('Inspect scan failed for %s.', self.scan_task)
            return ScanTask.FAILED

        try:
            logger.info('Inspect scan started for %s.', self.scan_task)
            status_code, api_version = utils.status(self.scan_task)
            if status_code == 200:
                self.conn_result = ConnectionResult.objects.filter(
                    scan_task=self.connect_scan_task.id).first()
                inspect_result = self.inspect_results.results.filter(
                    source__id=self.source.id).first()
                if inspect_result is None:
                    inspect_result = InspectionResult(
                        source=self.scan_task.source,
                        scan_task=self.scan_task)
                    inspect_result.save()
                    self.inspect_results.results.add(inspect_result)
                    self.inspect_results.save()
                self.inspect_result = inspect_result

                api = create(satellite_version, api_version,
                             self.scan_task, self.conn_result,
                             self.inspect_result)
                if not api:
                    logger.error('Satellite version %s with '
                                 'api version %s is not supported.',
                                 satellite_version, api_version)
                    logger.error('Inspect scan failed for %s.', self.scan_task)
                    return ScanTask.FAILED
                api.hosts_facts()
                logger.info('Inspect scan completed for %s.', self.scan_task)
            else:
                logger.error('Inspect scan failed for %s.', self.scan_task)
                return ScanTask.FAILED
        except SatelliteException as sat_error:
            logger.error('Satellite error encountered: %s', sat_error)
            logger.error('Inspect scan failed for %s.', self.scan_task)
            return ScanTask.FAILED
        except exceptions.ConnectionError as conn_error:
            logger.error('Satellite error encountered: %s', conn_error)
            logger.error('Inspect scan failed for %s.', self.scan_task)
            return ScanTask.FAILED

        return ScanTask.COMPLETED
