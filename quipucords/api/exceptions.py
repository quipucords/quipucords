"""Quipucords API exceptions."""

from rest_framework import status
from rest_framework.exceptions import APIException


class FailedDependencyError(APIException):
    """Custom APIException using status code 424."""

    status_code = status.HTTP_424_FAILED_DEPENDENCY
