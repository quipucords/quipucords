"""Model to track report publish requests to consoledot."""

from django.conf import settings
from django.db import models

from api.common.models import BaseModel


class PublishRequest(BaseModel):
    """Tracks the state of a user request to publish a report to consoledot."""

    class Status(models.TextChoices):
        """Possible states of a publish request."""

        PENDING = "pending"
        SENT = "sent"
        FAILED = "failed"

    class ErrorCode(models.TextChoices):
        """Machine-readable error reason for failed publish requests."""

        EXPIRED_TOKEN = "expired_token"  # noqa: S105
        NETWORK_UNREACHABLE = "network_unreachable"
        INVALID_REPORT = "invalid_report"
        SERVER_ERROR = "server_error"

    report = models.ForeignKey(
        "Report", on_delete=models.CASCADE, related_name="publish_requests"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    error_code = models.CharField(
        max_length=32, choices=ErrorCode.choices, blank=True, default=""
    )
    error_message = models.TextField(blank=True, default="")
