"""Test the v2 reports download API."""

import pytest
from rest_framework.reverse import reverse

from constants import DataSources
from tests.constants import (
    FILENAME_AGGREGATE_JSON,
    FILENAME_DEPLOYMENTS_CSV,
    FILENAME_DEPLOYMENTS_JSON,
    FILENAME_DETAILS_CSV,
    FILENAME_DETAILS_JSON,
    FILENAME_LIGHTSPEED_TGZ,
    FILENAME_SHA256SUM,
)
from tests.factories import DeploymentReportFactory
from tests.report_utils import extract_files_from_tarball
from tests.utils import fake_semver

TARBALL_ALWAYS_EXPECTED_FILENAMES = {
    FILENAME_AGGREGATE_JSON,
    FILENAME_SHA256SUM,
    FILENAME_DEPLOYMENTS_CSV,
    FILENAME_DEPLOYMENTS_JSON,
    FILENAME_DETAILS_CSV,
    FILENAME_DETAILS_JSON,
    FILENAME_LIGHTSPEED_TGZ,
}


@pytest.fixture
def sources(faker):
    """Return a sources list for a deployments report."""
    return [
        {
            "server_id": faker.uuid4(),
            "source_type": DataSources.NETWORK,
            "source_name": faker.slug(),
            "report_version": f"{fake_semver()}+{faker.sha1()}",
            "facts": [{"tomato": "pomodoro", "potato": "patata"}],
        }
    ]


@pytest.fixture
def deployments_report(sources):
    """Return a DeploymentsReport for one network source with two fingerprints."""
    deployments_report = DeploymentReportFactory(
        report__sources=sources, number_of_fingerprints=2
    )
    return deployments_report


@pytest.mark.django_db
class TestReportDownload:
    """Test the report download v2 API."""

    def test_invalid_report_id(self, client_logged_in, faker):
        """Test proper error if the report id specified is invalid."""
        report_id = faker.random_int()
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,))
        )
        assert not response.ok
        response_json = response.json()
        assert "No Report matches the given query" in response_json["detail"]

    def test_invalid_report_type(self, client_logged_in, deployments_report):
        """Test proper error if the report_type specified is invalid."""
        report_id = deployments_report.report.id
        bad_report_type = "bogustype"
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            data={"report_type": bad_report_type},
        )
        assert not response.ok
        response_json = response.json()
        assert (
            f"Unsupported report_type {bad_report_type} specified"
            in response_json["detail"]
        )

    def test_retrieve_default_tar(self, client_logged_in, sources, deployments_report):
        """Test that report download returns the default tarball."""
        report_id = deployments_report.report.id
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,))
        )
        assert response.ok
        assert response["Content-Type"] == "application/gzip; charset=utf-8"
        files_contents = extract_files_from_tarball(response.content)
        report_filenames = set(
            (
                name.format(report_id=report_id)
                for name in TARBALL_ALWAYS_EXPECTED_FILENAMES
            )
        )
        assert len(report_filenames) == len(TARBALL_ALWAYS_EXPECTED_FILENAMES)
        assert report_filenames == set(files_contents.keys())

    def test_retrieve_default_json(self, client_logged_in, sources, deployments_report):
        """Test that report download returns the default in JSON format."""
        report_id = deployments_report.report.id
        requested_type = "application/json"
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            headers={"Accept": requested_type},
        )
        assert response.ok
        assert response["Content-Type"] == requested_type
        report_json = response.json()
        assert report_json["report_id"] == report_id

    def test_retrieve_aggregate_json(
        self, client_logged_in, sources, deployments_report
    ):
        """Test that report download can return the Aggregate JSON report."""
        report_id = deployments_report.report.id
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            data={"report_type": "aggregate"},
        )
        assert response.ok
        assert response["Content-Type"] == "application/json"
        report_json = response.json()
        assert report_json["results"]

    def test_retrieve_deployments_json(
        self, client_logged_in, sources, deployments_report
    ):
        """Test that report download can return the Deployments JSON report."""
        report_id = deployments_report.report.id
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            data={"report_type": "deployments"},
        )
        assert response.ok
        assert response["Content-Type"] == "application/json"
        report_json = response.json()
        assert report_json["report_type"] == "deployments"
        assert report_json["report_id"] == report_id

    def test_retrieve_details_json(self, client_logged_in, sources, deployments_report):
        """Test that report download can return the Details JSON report."""
        report_id = deployments_report.report.id
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            data={"report_type": "details"},
        )
        assert response.ok
        assert response["Content-Type"] == "application/json"
        report_json = response.json()
        assert report_json["report_type"] == "details"
        assert report_json["report_id"] == report_id

    def test_retrieve_insights_json(
        self, client_logged_in, sources, deployments_report
    ):
        """Test that report download can return the Insights JSON report."""
        report_id = deployments_report.report.id
        response = client_logged_in.get(
            reverse("v2:download-report", args=(report_id,)),
            data={"report_type": "insights"},
        )
        assert response.ok
        assert response["Content-Type"] == "application/json"
        report_json = response.json()
        report_metadata = f"report_id_{report_id}/metadata.json"
        assert report_json[report_metadata]
        report_type = report_json[report_metadata]["source_metadata"]["report_type"]
        assert report_type == "insights"
