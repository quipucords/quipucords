"""Base class for integration tests."""

import tarfile
from io import BytesIO
from logging import getLogger
from time import sleep
from unittest import mock

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.models import InspectGroup, Report, ScanTask
from constants import DataSources
from fingerprinter.constants import (
    ENTITLEMENTS_KEY,
    META_DATA_KEY,
    PRODUCTS_KEY,
    SOURCES_KEY,
)
from tests.utils.facts import RawFactComparator
from utils import load_json_from_tarball

logger = getLogger(__name__)


class Smoker:
    """
    Base class for integration tests.

    Test classes inheriting from smoker require the following fixtures:
    - credential_payload
    - source_payload
    - expected_facts
    - fingerprint_fact_map
    - expected_middleware_names

    See integration tests that depend on Smoker for usage.

    NOTE: Due to the use of celery_worker fixture, django db must have transaction\
        support enabled.
    """

    MAX_RETRIES = 5
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "TBD"

    def test_sanity_check_source_type(self):
        """Test if SOURCE TYPE is a valid DataSource."""
        assert self.SOURCE_TYPE in DataSources.values

    @pytest.fixture
    def credential_id(self, client_logged_in, credential_payload):
        """Create credentials through api and return credentials identifier."""
        credential_payload.setdefault("cred_type", self.SOURCE_TYPE)
        response = client_logged_in.post(
            reverse("v1:credentials-list"),
            data=credential_payload,
        )
        assert response.status_code == status.HTTP_201_CREATED, response.json()
        return response.json()["id"]

    @pytest.fixture
    def source_id(self, client_logged_in, credential_id, source_payload):
        """Register source through api and return its identifier."""
        source_payload.setdefault("credentials", [credential_id])
        source_payload.setdefault("source_type", self.SOURCE_TYPE)
        source_payload.setdefault("name", self.SOURCE_NAME)
        response = client_logged_in.post(
            reverse("v1:source-list"),
            data=source_payload,
        )
        assert response.status_code == status.HTTP_201_CREATED, response.json()
        return response.json()["id"]

    @pytest.fixture
    def scan_id(self, client_logged_in, source_id):
        """Create a scan and return its identifier."""
        create_scan_response = client_logged_in.post(
            reverse("v1:scan-list"),
            data={"name": "test scan", "sources": [source_id]},
        )
        assert create_scan_response.status_code == status.HTTP_201_CREATED, (
            create_scan_response.json()
        )
        scan_id = create_scan_response.json()["id"]
        return scan_id

    @pytest.fixture
    def scan_response(self, client_logged_in, scan_id, celery_worker):
        """Start a scan job and poll its results endpoint until completion."""
        create_scan_job_response = client_logged_in.post(
            reverse("v1:scan-filtered-jobs", args=(scan_id,))
        )
        scan_detail_url = reverse("v1:scan-detail", args=(scan_id,))
        assert create_scan_job_response.status_code == status.HTTP_201_CREATED, (
            create_scan_job_response.json()
        )
        response = client_logged_in.get(scan_detail_url)
        assert response.ok, response.json()

        attempts = 1
        completed_status = {ScanTask.COMPLETED, ScanTask.CANCELED, ScanTask.FAILED}
        while (
            scan_status := response.json()["most_recent"]["status"]
        ) not in completed_status and attempts < self.MAX_RETRIES:
            attempts += 1
            backoff = 2**attempts
            sleep(backoff)
            response = client_logged_in.get(scan_detail_url)
            assert response.ok, response.json()

        scan_status = response.json()["most_recent"]["status"]
        assert scan_status == ScanTask.COMPLETED, response.json()

        return response

    @pytest.fixture
    def report_id(self, scan_response):
        """Return the latest report id from performed scan."""
        return scan_response.json()["most_recent"]["report_id"]

    @pytest.fixture
    def report(self, report_id):
        """Return the latest report object from performed scan."""
        return Report.objects.get(id=report_id)

    def test_raw_results(self, report: Report):
        """Ensure raw facts tied to inspect result are also directly bound to Report."""
        ig_from_tasks = set(
            InspectGroup.objects.filter(tasks__job__report_id=report.id)
            .values_list("id")
            .all()
        )
        ig_from_report = set(report.inspect_groups.values_list("id").all())
        assert ig_from_report == ig_from_tasks

    def test_details_report(
        self,
        client_logged_in,
        report_id,
        expected_facts,
    ):
        """Sanity check details report."""
        response = client_logged_in.get(
            reverse("v1:reports-details", args=(report_id,))
        )
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
        assert report_details_facts == expected_facts

    @pytest.fixture
    def expected_fingerprint_metadata(self, fingerprint_fact_map):
        """
        Return expected metadata dictionary.

        Dict contained within deployments report > system fingerprints.
        """
        metadata = {}
        for fingerprint_fact, raw_fact in fingerprint_fact_map.items():
            metadata[fingerprint_fact] = {
                "server_id": mock.ANY,
                "source_name": self.SOURCE_NAME,
                "source_type": self.SOURCE_TYPE,
                "raw_fact_key": RawFactComparator(raw_fact),
                "has_sudo": mock.ANY,
            }
        return metadata

    @pytest.fixture
    def expected_products(self):
        """Return expected products for deployments report."""
        return []

    def test_deployments_report(  # noqa: PLR0913
        self,
        client_logged_in,
        expected_fingerprint_metadata,
        fingerprint_fact_map,
        report_id,
        expected_fingerprints,
        expected_products,
    ):
        """Sanity check report deployments json structure."""
        response = client_logged_in.get(
            reverse("v1:reports-deployments", args=(report_id,))
        )
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
            PRODUCTS_KEY: expected_products,
            META_DATA_KEY: mock.ANY,
            **{fingerprint: mock.ANY for fingerprint in fingerprint_fact_map.keys()},
        }
        assert fingerprints_dict[META_DATA_KEY] == expected_fingerprint_metadata
        # Instead of looking for all fingerprints (our tests don't do that), lookup the
        # fingerprints expected (TBD in the fixture expected_fingerprints)
        target_fingerprints = {
            fp_name: fingerprints_dict[fp_name]
            for fp_name in expected_fingerprints.keys()
            if fp_name in fingerprints_dict
        }
        assert target_fingerprints == expected_fingerprints

    def test_compare_standalone_json_reports_with_tarball(
        self, client_logged_in, report_id
    ):
        """Compare individual reports with the ones bundled on the tarball endpoint."""
        details_response = client_logged_in.get(
            reverse("v1:reports-details", args=(report_id,))
        )
        assert details_response.ok, details_response.json()

        deployments_response = client_logged_in.get(
            reverse("v1:reports-deployments", args=(report_id,))
        )
        assert deployments_response.ok, deployments_response.json()

        full_report_response = client_logged_in.get(
            reverse("v1:reports-detail", args=(report_id,))
        )
        assert full_report_response.ok

        with tarfile.open(fileobj=BytesIO(full_report_response.content)) as tarball:
            tarball_details_dict = load_json_from_tarball(
                f"report_id_{report_id}/details-{report_id}.json", tarball
            )
            assert tarball_details_dict == details_response.json()

            tarball_deployments_dict = load_json_from_tarball(
                f"report_id_{report_id}/deployments-{report_id}.json", tarball
            )
            assert tarball_deployments_dict == deployments_response.json()
