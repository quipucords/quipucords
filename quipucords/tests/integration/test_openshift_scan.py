# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Integration test for OpenShift scan."""

import tarfile
from io import BytesIO
from logging import getLogger
from time import sleep
from unittest import mock

import pytest

from api.models import ScanTask
from fingerprinter.constants import (
    ENTITLEMENTS_KEY,
    META_DATA_KEY,
    PRODUCTS_KEY,
    SOURCES_KEY,
)
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import OCPDeployment, OCPProject
from tests.utils.facts import RawFactComparator
from utils import load_json_from_tarball

logger = getLogger(__name__)


@pytest.fixture
def expected_facts():
    """Set of expected facts on a OpenShift scan."""
    return {}


@pytest.fixture
def expected_middleware_names():
    """Middleware names."""
    return {}


@pytest.fixture
def fingerprint_fact_map():
    """Map fingerprint to raw fact name."""
    return {
        "name": "name",
        "container_images": "deployments",
        "container_labels": "deployments",
    }


@pytest.fixture
def expected_projects():
    """Return a list with OCP projects."""
    return [
        OCPProject(
            name="project name",
            labels={"some": "label"},
            deployments=[
                OCPDeployment(
                    name="deployment 1",
                    labels={"n": "1"},
                    container_images=["container-image-1:v1"],
                    init_container_images=[],
                ),
                OCPDeployment(
                    name="deployment 2",
                    labels={"n": "2"},
                    container_images=["container-image-1:v2"],
                    init_container_images=["some-other-image:ver"],
                ),
            ],
        ),
    ]


@pytest.fixture(autouse=True)
def patched_openshift_client(mocker, expected_projects):
    """Mock OpenShiftApi forcing it to return expected_projects."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_projects",
        return_value=expected_projects,
    )
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_deployments",
        return_value=expected_projects[0].deployments,
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestOpenShiftScan:
    """Smoke test network scan."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "openshift"

    @pytest.fixture
    def credential_id(self, django_client):
        """Create network credentials through api and return credentials identifier."""
        response = django_client.post(
            "credentials/",
            json={
                "name": "testing credential",
                "cred_type": self.SOURCE_TYPE,
                "auth_token": "<TOKEN>",
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture
    def source_id(self, django_client, credential_id):
        """Register source for network scan through api and return its identifier."""
        response = django_client.post(
            "sources/",
            json={
                "source_type": self.SOURCE_TYPE,
                "credentials": [credential_id],
                "hosts": ["ocp.host"],
                "name": self.SOURCE_NAME,
                "port": 7891,
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture
    def scan_id(self, django_client, source_id):
        """Create a scan and return its identifier."""
        create_scan_response = django_client.post(
            "scans/",
            json={"name": "test scan", "sources": [source_id]},
        )
        assert create_scan_response.ok, create_scan_response.text
        scan_id = create_scan_response.json()["id"]
        return scan_id

    @pytest.fixture
    def scan_response(self, django_client, scan_id):
        """Start a scan job and poll its results endpoint until completion."""
        create_scan_job_response = django_client.post(f"scans/{scan_id}/jobs/")
        assert create_scan_job_response.ok, create_scan_job_response.text

        response = django_client.get(f"scans/{scan_id}/")
        attempts = 1
        assert response.ok, response.text

        completed_status = {ScanTask.COMPLETED, ScanTask.CANCELED, ScanTask.FAILED}
        while (
            scan_status := response.json()["most_recent"]["status"]
        ) not in completed_status and attempts < self.MAX_RETRIES:
            attempts += 1
            backoff = 2**attempts
            sleep(backoff)
            response = django_client.get(f"scans/{scan_id}/")
            assert response.ok, response.text

        assert scan_status == ScanTask.COMPLETED, response.json()

        return response

    @pytest.fixture
    def report_id(self, scan_response):
        """Return the latest report id from performed scan."""
        return scan_response.json()["most_recent"]["report_id"]

    def test_details_report(self, django_client, expected_projects, report_id):
        """Sanity check details report."""
        response = django_client.get(f"reports/{report_id}/details/")
        assert response.ok, response.text
        report_details_dict = response.json()
        expected_details_report = {
            "report_id": report_id,
            "report_platform_id": mock.ANY,
            "report_type": "details",
            "report_version": mock.ANY,
            SOURCES_KEY: [
                {
                    "facts": mock.ANY,
                    "report_version": mock.ANY,
                    "server_id": mock.ANY,
                    "source_name": self.SOURCE_NAME,
                    "source_type": self.SOURCE_TYPE,
                }
            ],
        }
        assert report_details_dict == expected_details_report
        report_details_facts = report_details_dict[SOURCES_KEY][0]["facts"]
        assert report_details_facts == [p.to_dict() for p in expected_projects]

    @pytest.fixture
    def expected_fingerprint_metadata(self, fingerprint_fact_map):
        """
        Return expected metadata dictionary.

        Dict contained within deployments report > system fingerprints.
        """
        metadata = {}
        for fingerprint_fact, raw_fact in fingerprint_fact_map.items():
            metadata[fingerprint_fact] = dict(
                server_id=mock.ANY,
                source_name=self.SOURCE_NAME,
                source_type=self.SOURCE_TYPE,
                raw_fact_key=RawFactComparator(raw_fact),
                has_sudo=False,
            )
        return metadata

    def test_deployments_report(
        self,
        django_client,
        expected_fingerprint_metadata,
        fingerprint_fact_map,
        report_id,
    ):
        """Sanity check report deployments json structure."""
        response = django_client.get(f"reports/{report_id}/deployments/")
        assert response.ok, response.json()

        report_deployments_dict = response.json()
        assert report_deployments_dict == {
            "report_id": report_id,
            "status": ScanTask.COMPLETED,
            "report_type": "deployments",
            "report_version": mock.ANY,
            "report_platform_id": mock.ANY,
            "system_fingerprints": [mock.ANY],
        }

        fingerprints_dict = report_deployments_dict["system_fingerprints"][0]
        fingerprint_fact_names = set(fingerprints_dict[META_DATA_KEY].keys())
        assert fingerprint_fact_names == set(fingerprint_fact_map.keys())
        assert fingerprints_dict == {
            "id": mock.ANY,
            "deployment_report": mock.ANY,
            ENTITLEMENTS_KEY: [],
            SOURCES_KEY: [
                {
                    "server_id": mock.ANY,
                    "source_name": self.SOURCE_NAME,
                    "source_type": self.SOURCE_TYPE,
                }
            ],
            PRODUCTS_KEY: [],
            META_DATA_KEY: mock.ANY,
            **{fingerprint: mock.ANY for fingerprint in fingerprint_fact_map.keys()},
        }
        assert fingerprints_dict[META_DATA_KEY] == expected_fingerprint_metadata

    def test_compare_standalone_json_reports_with_tarball(
        self, django_client, report_id
    ):
        """Compare individual reports with the ones bundled on the tarball endpoint."""
        details_response = django_client.get(f"reports/{report_id}/details/")
        assert details_response.ok, details_response.json()

        deployments_response = django_client.get(f"reports/{report_id}/deployments/")
        assert deployments_response.ok, deployments_response.json()

        full_report_response = django_client.get(f"reports/{report_id}/")
        assert full_report_response.ok

        with tarfile.open(fileobj=BytesIO(full_report_response.content)) as tarball:
            tarball_details_dict = load_json_from_tarball(
                f"report_id_{report_id}/details.json", tarball
            )
            assert tarball_details_dict == details_response.json()

            tarball_deployments_dict = load_json_from_tarball(
                f"report_id_{report_id}/deployments.json", tarball
            )
            assert tarball_deployments_dict == deployments_response.json()
