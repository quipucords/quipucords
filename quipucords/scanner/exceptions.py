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
