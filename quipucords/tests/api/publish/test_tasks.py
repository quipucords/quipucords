"""Test the publish-to-consoledot Celery task."""

import http
import logging
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.auth_lightspeed import LIGHTSPEED_NAME, LIGHTSPEED_TYPE
from api.models import DeploymentsReport
from api.publish.model import PublishRequest
from api.publish.tasks import _get_ingress_url, publish_to_ingress, request_publish
from api.secure_token.model import SecureToken
from tests.factories import DeploymentReportFactory


@pytest.fixture()
def deployment_report():
    """Create a complete deployment report suitable for publishing."""
    return DeploymentReportFactory(status=DeploymentsReport.STATUS_COMPLETE)


@pytest.fixture()
def report(deployment_report):
    """Shortcut to the Report linked to deployment_report."""
    return deployment_report.report


@pytest.fixture()
def publish_request(report, qpc_user_simple):
    """Pending PublishRequest for the test report/user."""
    return PublishRequest.objects.create(report=report, user=qpc_user_simple)


@pytest.fixture()
def secure_token_valid(qpc_user_simple, faker):
    """Non-expired SecureToken for qpc_user_simple."""
    return SecureToken.objects.create(
        name=LIGHTSPEED_NAME,
        token_type=LIGHTSPEED_TYPE,
        user=qpc_user_simple,
        token=faker.lexify("?" * 64),
        expires_at=datetime.now(UTC) + timedelta(hours=4),
    )


@pytest.fixture()
def secure_token_expired(qpc_user_simple, faker):
    """Already-expired SecureToken for qpc_user_simple."""
    return SecureToken.objects.create(
        name=LIGHTSPEED_NAME,
        token_type=LIGHTSPEED_TYPE,
        user=qpc_user_simple,
        token=faker.lexify("?" * 64),
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )


class TestGetIngressUrl:
    """Test the ingress URL construction."""

    def test_default_https_url(self, settings):
        """Test that the default URL uses HTTPS."""
        settings.QUIPUCORDS_LIGHTSPEED_USE_HTTP = False
        settings.QUIPUCORDS_LIGHTSPEED_HOST = "console.redhat.com"
        settings.QUIPUCORDS_LIGHTSPEED_PORT = 443

        assert _get_ingress_url() == (
            "https://console.redhat.com:443/api/ingress/v1/upload"
        )

    def test_http_url(self, settings):
        """Test that HTTP mode builds the correct URL."""
        settings.QUIPUCORDS_LIGHTSPEED_USE_HTTP = True
        settings.QUIPUCORDS_LIGHTSPEED_HOST = "localhost"
        settings.QUIPUCORDS_LIGHTSPEED_PORT = 8080

        assert _get_ingress_url() == ("http://localhost:8080/api/ingress/v1/upload")


@pytest.mark.django_db
class TestPublishToIngressSuccess:
    """Test the happy path for publish_to_ingress."""

    def test_successful_publish(self, publish_request, secure_token_valid, mocker):
        """Test that a successful POST marks the request as SENT."""
        original_updated_at = publish_request.updated_at

        mock_tarball = BytesIO(b"fake-tarball-content")
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=mock_tarball,
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = True
        mock_post.return_value.text = "OK"

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.SENT
        assert publish_request.error_message == ""
        assert publish_request.updated_at > original_updated_at

    def test_post_includes_bearer_token(
        self, publish_request, secure_token_valid, mocker
    ):
        """Test that the POST request includes the Bearer auth header."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = True
        mock_post.return_value.text = "OK"

        publish_to_ingress(publish_request_id=publish_request.id)

        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == (
            f"Bearer {secure_token_valid.token}"
        )


@pytest.mark.django_db
class TestPublishToIngressAuthFailures:
    """Test authentication-related failures."""

    def test_missing_auth_token(self, publish_request):
        """Test that a missing token marks the request as FAILED."""
        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert publish_request.error_message == messages.PUBLISH_NO_AUTH_TOKEN

    def test_expired_auth_token(self, publish_request, secure_token_expired):
        """Test that an expired token marks the request as FAILED."""
        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert publish_request.error_message == messages.PUBLISH_TOKEN_EXPIRED

    def test_auth_rejected_by_server(self, publish_request, secure_token_valid, mocker):
        """Test that a 401 response marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = http.HTTPStatus.UNAUTHORIZED
        mock_post.return_value.text = "Invalid credentials"

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert messages.PUBLISH_AUTH_REJECTED % "Invalid credentials" in (
            publish_request.error_message
        )


@pytest.mark.django_db
class TestPublishToIngressNetworkFailures:
    """Test network-related failures."""

    def test_connection_error(self, publish_request, secure_token_valid, mocker):
        """Test that a ConnectionError marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        err_message = "Connection refused"
        mocker.patch(
            "api.publish.tasks.requests.post",
            side_effect=ConnectionError(err_message),
        )

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert err_message in publish_request.error_message

    def test_base_http_error(self, publish_request, secure_token_valid, mocker):
        """Test that a BaseHTTPError marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        err_message = "urllib3 error"
        mocker.patch(
            "api.publish.tasks.requests.post",
            side_effect=BaseHTTPError(err_message),
        )

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert err_message in publish_request.error_message

    def test_ingress_not_found(self, publish_request, secure_token_valid, mocker):
        """Test that a 404 response marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = http.HTTPStatus.NOT_FOUND
        mock_post.return_value.text = "Not Found"

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert publish_request.error_message == messages.PUBLISH_INGRESS_NOT_FOUND

    def test_ingress_server_error(self, publish_request, secure_token_valid, mocker):
        """Test that a 500 response marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        mock_post.return_value.text = "Internal Server Error"

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert "Internal Server Error" in publish_request.error_message

    def test_unexpected_status_code(self, publish_request, secure_token_valid, mocker):
        """Test that an unexpected HTTP status marks the request as FAILED."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            return_value=BytesIO(b"data"),
        )
        mock_post = mocker.patch("api.publish.tasks.requests.post")
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = http.HTTPStatus.BAD_GATEWAY
        mock_post.return_value.text = "Bad Gateway"

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert "502" in publish_request.error_message
        assert "Bad Gateway" in publish_request.error_message


@pytest.mark.django_db
class TestPublishToIngressEdgeCases:
    """Test edge cases for publish_to_ingress."""

    def test_nonexistent_publish_request(self, faker, caplog):
        """Test that a missing PublishRequest logs an error and returns."""
        nonexistent_id = faker.pyint(min_value=990000, max_value=999999)
        with caplog.at_level(logging.ERROR, logger="api.publish.tasks"):
            publish_to_ingress(publish_request_id=nonexistent_id)
        assert str(nonexistent_id) in caplog.text

    def test_payload_generation_failure(
        self, publish_request, secure_token_valid, mocker
    ):
        """Test that an unexpected error during payload generation is handled."""
        mocker.patch(
            "api.publish.tasks.generate_insights_tarball",
            side_effect=RuntimeError("serializer exploded"),
        )

        publish_to_ingress(publish_request_id=publish_request.id)

        publish_request.refresh_from_db()
        assert publish_request.status == PublishRequest.Status.FAILED
        assert "serializer exploded" in publish_request.error_message


@pytest.mark.django_db
class TestRequestPublish:
    """Test the request_publish helper."""

    def test_creates_publish_request_and_dispatches_task(
        self, report, qpc_user_simple, mocker
    ):
        """Test that request_publish creates a PublishRequest and calls delay."""
        mock_delay = mocker.patch("api.publish.tasks.publish_to_ingress.delay")

        result = request_publish(report, qpc_user_simple)

        assert isinstance(result, PublishRequest)
        assert result.report == report
        assert result.user == qpc_user_simple
        assert result.status == PublishRequest.Status.PENDING
        mock_delay.assert_called_once_with(publish_request_id=result.id)
