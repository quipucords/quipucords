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
from django.db import transaction
from api.models import (SystemConnectionResult)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class SatelliteException(Exception):
    """Exception for Satellite interaction."""

    pass


class SatelliteInterface(object):
    """Generic interface for dealing with Satellite."""

    def __init__(self, scan_task, conn_result):
        """Set context for interface."""
        self.scan_task = scan_task
        self.conn_result = conn_result

    @transaction.atomic
    def initialize_stats(self, systems_count):
        """Set initial status based on system counts.

        :param systems_count: The system count
        """
        self.scan_task.systems_count = systems_count
        self.scan_task.systems_scanned = 0
        self.scan_task.save()

    @transaction.atomic
    def record_result(self, name, credential):
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

        self.scan_task.systems_scanned += 1
        self.scan_task.save()

    def host_count(self):
        """Obtain the count of managed hosts."""
        pass

    def hosts(self):
        """Obtain the managed hosts."""
        pass
