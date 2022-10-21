# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Scanner exceptions."""

from api.models import ScanTask


class ScanException(Exception):
    """Generic scanner exception."""


class ScanInterruptException(ScanException):
    """
    Generic Interrupt Exception.

    Classes inheriting this one should set constant STATUS to one of ScanTask statuses.
    """

    STATUS = None


class ScanCancelException(ScanInterruptException):
    """Scan cancel exception."""

    STATUS = ScanTask.CANCELED


class ScanPauseException(ScanInterruptException):
    """Scan pause exception."""

    STATUS = ScanTask.PAUSED


class ScanFailureError(ScanException):
    """
    Exception for scan failures.

    Recommendation
    --------------

    inside ScanTaskRunner.execute_task implementations, call

        raise ScanFailureError("<error message>")

    instead of

        return "<error message>", ScanTask.FAILED

    """

    def __init__(self, message, *args):
        """Initialize exception."""
        self.message = message
        super().__init__(message, *args)
