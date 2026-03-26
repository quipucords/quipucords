"""Lightspeed integration."""

from api.auth.auth_lightspeed import get_lightspeed_secure_token
from api.common.entities import ReportEntity
from api.common.enumerators import AuthStatus, LightspeedCannotPublishReason
from api.exceptions import FailedDependencyError
from api.insights_report.payload import validate_deployment_report_status
from api.models import Report, SystemFingerprint

AUTH_CANNOT_PUBLISH_REASON_MAP = {
    # AuthStatus.VALID is omitted because it means Lightspeed CAN be published
    AuthStatus.PENDING: LightspeedCannotPublishReason.AUTH_PENDING,
    AuthStatus.FAILED: LightspeedCannotPublishReason.AUTH_FAILED,
    AuthStatus.EXPIRED: LightspeedCannotPublishReason.AUTH_EXPIRED,
    AuthStatus.MISSING: LightspeedCannotPublishReason.AUTH_MISSING,
    None: LightspeedCannotPublishReason.AUTH_MISSING,
}


def get_cannot_publish_reason(
    report: Report, user
) -> LightspeedCannotPublishReason | None:
    """
    Give reason why report can't be published to Lightspeed.

    None means there is no reason why report couldn't be published, which
    means that it CAN be published.

    Note that this controls only our attempt at publishing. Report can still be
    rejected by remote service for reasons we can't predict.
    """
    lightspeed_secure_token = get_lightspeed_secure_token(user)
    lightspeed_auth_status = None
    try:
        lightspeed_auth_status = AuthStatus(
            lightspeed_secure_token.metadata.get("status")
        )
    except (AttributeError, ValueError):
        # if there's no token, metadata has no status, or somehow status is not one of
        # AuthStatus values, fall back to status = None and act as if token was missing
        pass

    if auth_issue := AUTH_CANNOT_PUBLISH_REASON_MAP.get(lightspeed_auth_status):
        return auth_issue

    try:
        validate_deployment_report_status(report.deployment_report)
    except (AttributeError, FailedDependencyError):
        return LightspeedCannotPublishReason.NOT_COMPLETE

    try:
        ReportEntity.from_report_id(report.id)
    except SystemFingerprint.DoesNotExist:
        return LightspeedCannotPublishReason.NO_HOSTS

    return None


def get_can_publish(report: Report, user) -> bool:
    """Whether report can be published to Lightspeed."""
    return get_cannot_publish_reason(report, user) is None
