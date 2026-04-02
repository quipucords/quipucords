"""Celery tasks for publishing reports to consoledot."""

import http
import logging

import celery
import requests
from django.conf import settings
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.auth_lightspeed import get_lightspeed_secure_token
from api.insights_report.payload import generate_insights_tarball
from api.publish.exceptions import PublishError
from api.publish.model import PublishRequest

logger = logging.getLogger(__name__)

INGRESS_UPLOAD_PATH = "/api/ingress/v1/upload"
CONTENT_TYPE = "application/vnd.redhat.qpc.tar+tgz"


def _get_ingress_url():
    """Build the full ingress upload URL from settings."""
    protocol = "http" if settings.QUIPUCORDS_LIGHTSPEED_USE_HTTP else "https"
    host = settings.QUIPUCORDS_LIGHTSPEED_HOST
    port = settings.QUIPUCORDS_LIGHTSPEED_PORT
    return f"{protocol}://{host}:{port}{INGRESS_UPLOAD_PATH}"


def _get_auth_token(user):
    """Retrieve and validate the user's auth token."""
    secure_token = get_lightspeed_secure_token(user)
    if not secure_token or not secure_token.token:
        raise PublishError(
            messages.PUBLISH_NO_AUTH_TOKEN,
            error_code=PublishRequest.ErrorCode.EXPIRED_TOKEN,
        )

    if secure_token.is_expired():
        raise PublishError(
            messages.PUBLISH_TOKEN_EXPIRED,
            error_code=PublishRequest.ErrorCode.EXPIRED_TOKEN,
        )

    return secure_token.token


def _post_to_ingress(report_id, tarball, auth_token):
    """POST the tarball to the ingress endpoint."""
    ingress_url = _get_ingress_url()
    files = {"file": (f"report_{report_id}", tarball, CONTENT_TYPE)}
    headers = {"Authorization": f"Bearer {auth_token}"}

    logger.info("Posting report %d to %s", report_id, ingress_url)

    try:
        response = requests.post(
            ingress_url,
            files=files,
            headers=headers,
            timeout=settings.QUIPUCORDS_AUTH_LIGHTSPEED_TIMEOUT,
            verify=settings.QUIPUCORDS_LIGHTSPEED_SSL_VERIFY,
        )
    except (ConnectionError, BaseHTTPError) as err:
        raise PublishError(
            messages.PUBLISH_CONNECTION_ERROR % err,
            error_code=PublishRequest.ErrorCode.NETWORK_UNREACHABLE,
        ) from err

    if response.ok:
        logger.info(
            "Report %d published successfully. Response: %s",
            report_id,
            response.text,
        )
        return

    status = response.status_code
    if status == http.HTTPStatus.UNAUTHORIZED:
        raise PublishError(
            messages.PUBLISH_AUTH_REJECTED % response.text,
            error_code=PublishRequest.ErrorCode.EXPIRED_TOKEN,
        )
    elif http.HTTPStatus.BAD_REQUEST <= status < http.HTTPStatus.INTERNAL_SERVER_ERROR:
        raise PublishError(
            messages.PUBLISH_CLIENT_ERROR % (status, response.text),
            error_code=PublishRequest.ErrorCode.SERVER_ERROR,
        )
    elif status >= http.HTTPStatus.INTERNAL_SERVER_ERROR:
        raise PublishError(
            messages.PUBLISH_SERVER_ERROR % (status, response.text),
            error_code=PublishRequest.ErrorCode.SERVER_ERROR,
        )
    else:
        raise PublishError(
            messages.PUBLISH_UNEXPECTED_RESPONSE % (status, response.text),
            error_code=PublishRequest.ErrorCode.SERVER_ERROR,
        )


@celery.shared_task
def publish_to_ingress(*, publish_request_id):
    """Publish a report tarball to the consoledot ingress endpoint."""
    try:
        publish_request = PublishRequest.objects.select_related("report", "user").get(
            id=publish_request_id
        )
    except PublishRequest.DoesNotExist:
        logger.error("PublishRequest %d not found, cannot publish.", publish_request_id)
        return

    report_id = publish_request.report_id

    logger.info(
        "Publishing report %d for user %s (PublishRequest %d).",
        report_id,
        publish_request.user,
        publish_request.id,
    )

    try:
        auth_token = _get_auth_token(publish_request.user)
        tarball = generate_insights_tarball(report_id)
        _post_to_ingress(report_id, tarball, auth_token)
    except PublishError as err:
        logger.error(
            "Publish request %d for report %d failed: %s",
            publish_request.id,
            report_id,
            err,
        )
        _save_result(
            publish_request,
            PublishRequest.Status.FAILED,
            error_message=str(err),
            error_code=err.error_code,
        )
        return
    except Exception as err:
        logger.exception(
            "Publish request %d for report %d failed unexpectedly: %s",
            publish_request.id,
            report_id,
            err,
        )
        _save_result(
            publish_request,
            PublishRequest.Status.FAILED,
            error_message=messages.PUBLISH_PAYLOAD_FAILED % err,
            error_code=PublishRequest.ErrorCode.SERVER_ERROR,
        )
        return

    _save_result(publish_request, PublishRequest.Status.SENT)


def _save_result(publish_request, status, error_message="", error_code=""):
    """Save task result, skipping if a newer publish has taken over."""
    publish_request.refresh_from_db()
    if publish_request.status != PublishRequest.Status.PENDING:
        logger.warning(
            "PublishRequest %d is no longer pending (status=%s), skipping update.",
            publish_request.id,
            publish_request.status,
        )
        return
    publish_request.status = status
    publish_request.error_code = error_code
    publish_request.error_message = error_message
    publish_request.save()


def request_publish(report, user):
    """Create a new PublishRequest and dispatch the Celery task."""
    publish_request = PublishRequest.objects.create(
        report=report,
        user=user,
    )
    publish_to_ingress.delay(publish_request_id=publish_request.id)
    logger.info(
        "PublishRequest %d created for report %d by user %s.",
        publish_request.id,
        report.id,
        user,
    )
    return publish_request
