"""Test Deployment models."""

import pytest

from tests.factories import DeploymentReportFactory


@pytest.mark.django_db
def test_fingerprint_source_types():
    """Test fingerprint method for "source_types"."""
    deployment_report = DeploymentReportFactory(number_of_fingerprints=1)
    fingerprint = deployment_report.system_fingerprints.first()
    assert isinstance(fingerprint.source_types(), set)
    assert fingerprint.source_types() == {
        source["source_type"] for source in fingerprint.sources
    }
