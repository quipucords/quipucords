"""Quipucords API exceptions."""

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class UnprocessableEntity(APIException):
    """APIException for status code 422 - Unprocessable Entity."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = _("Unprocessable Entity.")
    default_code = "unprocessable_entity"


class FailedDependencyError(APIException):
    """Custom APIException using status code 424."""

    status_code = status.HTTP_424_FAILED_DEPENDENCY
