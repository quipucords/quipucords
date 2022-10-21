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
"""Satellite API Interface."""
import json
import logging

from django.db import transaction

from api.models import (
    RawFact,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
    SystemInspectionResult,
)
from scanner.exceptions import ScanCancelException, ScanPauseException

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

SATELLITE_VERSION_5 = "5"
SATELLITE_VERSION_6 = "6"


class SatelliteAuthException(Exception):
    """Exception for Satellite Authentication interaction."""


class SatelliteException(Exception):
    """Exception for Satellite interaction."""


class SatelliteCancelException(ScanCancelException):
    """Exception for Satellite Cancel interrupt."""


class SatellitePauseException(ScanPauseException):
    """Exception for Satellite Pause interrupt."""


class SatelliteInterface:
    """Generic interface for dealing with Satellite."""

    def __init__(self, scan_job, scan_task):
        """Set context for interface."""
        self.scan_job = scan_job
        if scan_job.options is None:
            self.max_concurrency = ScanOptions.get_default_forks()
        else:
            self.max_concurrency = scan_job.options.max_concurrency

        if scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            self.connect_scan_task = scan_task
            self.inspect_scan_task = None
        else:
            self.connect_scan_task = scan_task.prerequisites.first()
            self.inspect_scan_task = scan_task
        self.source = scan_task.source

    @transaction.atomic
    def record_conn_result(self, name, credential):
        """Record a new result.

        :param name: The host name
        :param credential: The authentication credential
        """
        sys_result = SystemConnectionResult(
            name=name,
            source=self.source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=self.connect_scan_task.connection_result,
        )
        sys_result.save()

        self.connect_scan_task.increment_stats(name, increment_sys_scanned=True)

    @transaction.atomic
    def record_inspect_result(self, name, facts, status=SystemInspectionResult.SUCCESS):
        """Record a new result.

        :param name: The host name
        :param facts: The dictionary of facts
        :param status: The status of the inspection
        """
        sys_result = SystemInspectionResult(
            name=name,
            source=self.source,
            status=status,
            task_inspection_result=self.inspect_scan_task.inspection_result,
        )
        sys_result.save()

        if status == SystemInspectionResult.SUCCESS:
            for key, val in facts.items():
                if val is not None:
                    final_value = json.dumps(val)
                    stored_fact = RawFact(
                        name=key, value=final_value, system_inspection_result=sys_result
                    )
                    stored_fact.save()

        if status == SystemInspectionResult.SUCCESS:
            self.inspect_scan_task.increment_stats(name, increment_sys_scanned=True)
        elif status == SystemInspectionResult.UNREACHABLE:
            self.inspect_scan_task.increment_stats(name, increment_sys_unreachable=True)
        else:
            self.inspect_scan_task.increment_stats(name, increment_sys_failed=True)

    def host_count(self):
        """Obtain the count of managed hosts."""
        pass

    def hosts(self):
        """Obtain the managed hosts."""
        pass

    def hosts_facts(self, manager_interrupt):
        """Obtain the managed hosts detail raw facts."""
        pass
