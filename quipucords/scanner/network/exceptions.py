"""Exceptions used by network scan."""

from scanner.exceptions import ScanCancelException, ScanPauseException


class NetworkCancelException(ScanCancelException):
    """Exception for Network Cancel interrupt."""


class NetworkPauseException(ScanPauseException):
    """Exception for Network Pause interrupt."""


class ScannerException(Exception):
    """Exception for issues detected during scans."""

    def __init__(self, message=""):
        """Exception for issues detected during scans.

        :param message: An error message describing the problem encountered
        during scan.
        """
        self.message = f"Scan task failed.  Error: {message}"
        super().__init__(self.message)
