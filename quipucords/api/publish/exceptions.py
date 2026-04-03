"""Publish custom exceptions."""


class PublishError(Exception):
    """Raised when a publish operation fails."""

    def __init__(self, message, error_code=""):
        super().__init__(message)
        self.error_code = error_code
