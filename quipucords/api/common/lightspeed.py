"""Lightspeed integration."""

from api.common.entities import ReportEntity
from api.common.enumerators import LightspeedCannotPublishReason
from api.exceptions import FailedDependencyError
from api.insights_report.view import validate_deployment_report_status
from api.models import Report, SystemFingerprint


def get_cannot_publish_reason(report: Report) -> LightspeedCannotPublishReason | None:
    """
    Give reason why report can't be published to Lightspeed.

    None means there is no reason why report couldn't be published, which
    means that it CAN be published.

    Note that this controls only our attempt at publishing. Report can still be
    rejected by remote service for reasons we can't predict.
    """
    # FIXME: add other LightspeedCannotPublishReason values

    try:
        validate_deployment_report_status(report.deployment_report)
    except (AttributeError, FailedDependencyError):
        return LightspeedCannotPublishReason.NOT_COMPLETE

    try:
        ReportEntity.from_report_id(report.id)
    except SystemFingerprint.DoesNotExist:
        return LightspeedCannotPublishReason.NO_HOSTS

    return None
