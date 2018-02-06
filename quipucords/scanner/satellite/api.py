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

import logging
import json
from django.db import transaction
from api.models import (SystemConnectionResult,
                        SystemInspectionResult,
                        RawFact)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class SatelliteException(Exception):
    """Exception for Satellite interaction."""

    pass


class SatelliteInterface(object):
    """Generic interface for dealing with Satellite."""

    def __init__(self, scan_task, conn_result, inspect_result=None):
        """Set context for interface."""
        self.scan_task = scan_task
        self.conn_result = conn_result
        self.inspect_result = inspect_result

    @transaction.atomic
    def initialize_stats(self, systems_count):
        """Set initial status based on system counts.

        :param systems_count: The system count
        """
        self.scan_task.update_stats(
            'INITIAL STATELLITE STATS', sys_count=systems_count)

    @transaction.atomic
    def record_conn_result(self, name, credential):
        """Record a new result.

        :param name: The host name
        :param credential: The authentication credential
        """
        sys_result = SystemConnectionResult(
            name=name,
            credential=credential,
            status=SystemConnectionResult.SUCCESS)
        sys_result.save()

        self.conn_result.systems.add(sys_result)
        self.conn_result.save()

        self.scan_task.increment_stats(name, increment_sys_scanned=True)

    @transaction.atomic
    def record_inspect_result(self, name, facts):
        """Record a new result.

        :param name: The host name
        :param facts: The dictionary of facts
        """
        sys_result = SystemInspectionResult(
            name=name,
            status=SystemInspectionResult.SUCCESS)
        sys_result.save()

        for key, val in facts.items():
            if val is not None:
                final_value = json.dumps(val)
                stored_fact = RawFact(name=key, value=final_value)
                stored_fact.save()
                sys_result.facts.add(stored_fact)

        self.inspect_result.systems.add(sys_result)
        self.inspect_result.save()

        self.scan_task.increment_stats(name, increment_sys_scanned=True)

    def host_count(self):
        """Obtain the count of managed hosts."""
        pass

    def hosts(self):
        """Obtain the managed hosts."""
        pass

    def hosts_facts(self):
        """Obtain the managed hosts detail raw facts."""
        pass
