"""Test the lightspeed module."""

import pytest

from api.auth.lightspeed.auth import update_secure_token_status
from api.common.enumerators import AuthStatus, LightspeedCannotPublishReason
from api.common.lightspeed import get_cannot_publish_reason
from api.deployments_report.model import DeploymentsReport
from tests.factories import DeploymentReportFactory, ReportFactory
from tests.utils.auth import create_lightspeed_secure_token


@pytest.mark.django_db
def test_get_can_publish_and_reason_report_can_publish(user_with_lightspeed_token):
    """Test report with complete deployment and hosts can be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
        number_of_fingerprints=3,
    )
    report = deployment_report.report

    assert get_cannot_publish_reason(report, user_with_lightspeed_token) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "auth_status, expected_cannot_publish_reason",
    (
        pytest.param(
            AuthStatus.PENDING, LightspeedCannotPublishReason.AUTH_PENDING, id="pending"
        ),
        pytest.param(
            AuthStatus.FAILED, LightspeedCannotPublishReason.AUTH_FAILED, id="failed"
        ),
        pytest.param(
            AuthStatus.EXPIRED, LightspeedCannotPublishReason.AUTH_EXPIRED, id="expired"
        ),
        pytest.param(
            AuthStatus.MISSING, LightspeedCannotPublishReason.AUTH_MISSING, id="missing"
        ),
    ),
)
def test_get_can_publish_and_reason_token_issues(
    qpc_user_simple,
    lightspeed_user_metadata,
    auth_status,
    expected_cannot_publish_reason,
):
    """Test report cannot be published due to various authentication issues."""
    report = ReportFactory(deployment_report=None)
    lightspeed_token = create_lightspeed_secure_token(
        qpc_user_simple, lightspeed_user_metadata
    )
    update_secure_token_status(lightspeed_token, auth_status)

    reason = get_cannot_publish_reason(report, qpc_user_simple)
    assert reason == expected_cannot_publish_reason


@pytest.mark.django_db
def test_get_can_publish_and_reason_without_deployment_report(
    user_with_lightspeed_token,
):
    """Test report without deployment report cannot be published."""
    report = ReportFactory(deployment_report=None)

    reason = get_cannot_publish_reason(report, user_with_lightspeed_token)
    assert reason == LightspeedCannotPublishReason.NOT_COMPLETE


@pytest.mark.django_db
def test_get_can_publish_and_reason_incomplete_deployment_report(
    user_with_lightspeed_token,
):
    """Test report with incomplete deployment report cannot be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_PENDING,
    )
    report = deployment_report.report

    reason = get_cannot_publish_reason(report, user_with_lightspeed_token)

    assert reason == LightspeedCannotPublishReason.NOT_COMPLETE


@pytest.mark.django_db
def test_get_can_publish_and_reason_no_hosts(user_with_lightspeed_token):
    """Test report with deployment report but no hosts cannot be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
        number_of_fingerprints=0,
    )
    report = deployment_report.report

    reason = get_cannot_publish_reason(report, user_with_lightspeed_token)

    assert reason == LightspeedCannotPublishReason.NO_HOSTS
