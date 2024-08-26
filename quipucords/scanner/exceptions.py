"""Scanner exceptions."""


class ScanError(Exception):
    """Generic scanner exception."""


class ScanFailureError(ScanError):
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
