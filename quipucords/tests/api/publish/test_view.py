"""Test the publish report API endpoint."""

import pytest
from rest_framework.reverse import reverse

from api import messages
from api.models import DeploymentsReport
from api.publish.model import PublishRequest
from tests.factories import DeploymentReportFactory, ReportFactory

pytestmark = pytest.mark.django_db

PUBLISH_URL_NAME = "v2:report-publish"


def _url(report_id):
    return reverse(PUBLISH_URL_NAME, args=(report_id,))


@pytest.fixture()
def publishable_report():
    """Report with a complete deployment report and hosts."""
    dr = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
        number_of_fingerprints=3,
    )
    return dr.report


@pytest.fixture()
def unpublishable_report():
    """Report without a deployment report."""
    return ReportFactory(deployment_report=None)


def test_post_publish_success(
    client_logged_in, publishable_report, user_with_lightspeed_token, mocker
):
    """Test POST creates a PublishRequest and returns 201."""
    mocker.patch("api.publish.tasks.publish_to_ingress.delay")

    response = client_logged_in.post(_url(publishable_report.id))

    assert response.status_code == 201
    data = response.json()
    assert data["report_id"] == publishable_report.id
    assert data["status"] == "pending"
    assert data["error_code"] == ""
    assert data["error_message"] == ""
    assert "created_at" in data
    assert "updated_at" in data


def test_post_publish_report_not_found(client_logged_in):
    """Test POST with nonexistent report returns 404."""
    response = client_logged_in.post(_url(999999))

    assert response.status_code == 404


def test_post_publish_not_publishable(client_logged_in, unpublishable_report):
    """Test POST with non-publishable report returns 400."""
    response = client_logged_in.post(_url(unpublishable_report.id))

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == PublishRequest.ErrorCode.INVALID_REPORT
    assert "cannot be published" in data["message"]


def test_post_publish_already_pending(
    client_logged_in, publishable_report, user_with_lightspeed_token, mocker
):
    """Test POST when a PENDING request exists returns 409."""
    mocker.patch("api.publish.tasks.publish_to_ingress.delay")
    client_logged_in.post(_url(publishable_report.id))

    response = client_logged_in.post(_url(publishable_report.id))

    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "already_pending"
    assert data["message"] == messages.PUBLISH_ALREADY_PENDING


def test_post_publish_after_failed(
    client_logged_in, publishable_report, user_with_lightspeed_token, mocker
):
    """Test POST after a FAILED request resets and returns 201."""
    mocker.patch("api.publish.tasks.publish_to_ingress.delay")
    client_logged_in.post(_url(publishable_report.id))
    pr = PublishRequest.objects.get(report=publishable_report)
    pr.status = PublishRequest.Status.FAILED
    pr.error_message = "something broke"
    pr.save()

    response = client_logged_in.post(_url(publishable_report.id))

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["error_code"] == ""
    assert response.json()["error_message"] == ""


def test_post_publish_after_sent(
    client_logged_in, publishable_report, user_with_lightspeed_token, mocker
):
    """Test POST after a SENT request creates a new one and returns 201."""
    mocker.patch("api.publish.tasks.publish_to_ingress.delay")
    client_logged_in.post(_url(publishable_report.id))
    pr = PublishRequest.objects.get(report=publishable_report)
    pr.status = PublishRequest.Status.SENT
    pr.save()

    response = client_logged_in.post(_url(publishable_report.id))

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_post_publish_unauthenticated(client_logged_out, publishable_report):
    """Test POST without authentication returns 401."""
    response = client_logged_out.post(_url(publishable_report.id))

    assert response.status_code == 401


def test_get_publish_status(client_logged_in, publishable_report, qpc_user_simple):
    """Test GET returns the existing PublishRequest."""
    PublishRequest.objects.create(
        report=publishable_report,
        user=qpc_user_simple,
        status=PublishRequest.Status.SENT,
    )

    response = client_logged_in.get(_url(publishable_report.id))

    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == publishable_report.id
    assert data["status"] == "sent"
    assert data["error_code"] == ""


def test_get_publish_status_returns_latest(
    client_logged_in, publishable_report, qpc_user_simple
):
    """Test GET returns the most recent PublishRequest when multiple exist."""
    PublishRequest.objects.create(
        report=publishable_report,
        user=qpc_user_simple,
        status=PublishRequest.Status.FAILED,
        error_message="old failure",
    )
    latest = PublishRequest.objects.create(
        report=publishable_report,
        user=qpc_user_simple,
        status=PublishRequest.Status.PENDING,
    )

    response = client_logged_in.get(_url(publishable_report.id))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["error_code"] == ""
    assert data["error_message"] == ""
    assert data["created_at"] == latest.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def test_get_publish_status_no_request(client_logged_in, publishable_report):
    """Test GET when no PublishRequest exists returns 404."""
    response = client_logged_in.get(_url(publishable_report.id))

    assert response.status_code == 404


def test_get_publish_status_report_not_found(client_logged_in):
    """Test GET with nonexistent report returns 404."""
    response = client_logged_in.get(_url(999999))

    assert response.status_code == 404


def test_get_publish_status_unauthenticated(client_logged_out, publishable_report):
    """Test GET without authentication returns 401."""
    response = client_logged_out.get(_url(publishable_report.id))

    assert response.status_code == 401
