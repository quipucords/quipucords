"""Test the lightspeed module."""

import pytest

from api.common.enumerators import LightspeedCannotPublishReason
from api.common.lightspeed import get_cannot_publish_reason
from api.deployments_report.model import DeploymentsReport
from tests.factories import DeploymentReportFactory, ReportFactory


@pytest.mark.django_db
def test_get_can_publish_and_reason_report_can_publish():
    """Test report with complete deployment and hosts can be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
        number_of_fingerprints=3,
    )
    report = deployment_report.report

    assert get_cannot_publish_reason(report) is None


@pytest.mark.django_db
def test_get_can_publish_and_reason_without_deployment_report():
    """Test report without deployment report cannot be published."""
    report = ReportFactory(deployment_report=None)

    reason = get_cannot_publish_reason(report)
    assert reason == LightspeedCannotPublishReason.NOT_COMPLETE


@pytest.mark.django_db
def test_get_can_publish_and_reason_incomplete_deployment_report():
    """Test report with incomplete deployment report cannot be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_PENDING,
    )
    report = deployment_report.report

    reason = get_cannot_publish_reason(report)

    assert reason == LightspeedCannotPublishReason.NOT_COMPLETE


@pytest.mark.django_db
def test_get_can_publish_and_reason_no_hosts():
    """Test report with deployment report but no hosts cannot be published."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
        number_of_fingerprints=0,
    )
    report = deployment_report.report

    reason = get_cannot_publish_reason(report)

    assert reason == LightspeedCannotPublishReason.NO_HOSTS
