"""Test the report API."""

from unittest import mock

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.common.common_report import create_report_version
from api.models import Credential, ScanTask, ServerInformation, Source
from constants import DataSources
from tests.scanner.test_util import create_scan_job


class TestAsyncMergeReports:
    """Tests against the Deployment reports function."""

    @pytest.fixture
    def source_credential(self, faker):
        """Return a Credential for a Network Source."""
        return Credential.objects.create(
            name=faker.slug(),
            cred_type=DataSources.NETWORK,
            username=faker.slug(),
            password=faker.slug(),
            become_password=None,
            ssh_keyfile=None,
        )

    @pytest.fixture
    def network_source(self, source_credential, faker):
        """Return a Network Source."""
        return Source.objects.create(
            name=faker.slug(), source_type=DataSources.NETWORK, hosts=[faker.ipv4()]
        )

    @pytest.fixture
    def server_id(self):
        """Return a Server Id."""
        return ServerInformation.create_or_retrieve_server_id()

    def merge_details_from_source_expect_201(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = django_client.post(reverse("v1:reports-merge-jobs"), json=data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def merge_details_from_source_expect_400(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = django_client.post(reverse("v1:reports-merge-jobs"), json=data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        return response.json()

    ##############################################################
    # Test Async Report Merge
    ##############################################################

    def test_greenpath_create(self, server_id, network_source, django_client):
        """Create report merge job object via API."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                    "facts": [{"key": "value"}],
                }
            ],
        }

        response_json = self.merge_details_from_source_expect_201(
            request_json, django_client
        )

        expected = {
            "report_id": mock.ANY,
            "scan_type": "fingerprint",
            "status": "created",
            "status_message": "Job is created.",
        }
        assert "id" in response_json
        job_id = response_json.pop("id")
        assert response_json == expected

        url = reverse("v1:reports-merge-jobs-detail", args=(job_id,))
        get_response = django_client.get(url)
        assert get_response.status_code == status.HTTP_200_OK

    def test_success_create_with_identical_sources(
        self, server_id, network_source, django_client
    ):
        """Create report merge job with two identical sources."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                    "facts": [{"key": "value"}],
                },
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                    "facts": [{"key": "value"}],
                },
            ],
        }

        response_json = self.merge_details_from_source_expect_201(
            request_json, django_client
        )

        expected = {
            "report_id": mock.ANY,
            "scan_type": "fingerprint",
            "status": "created",
            "status_message": "Job is created.",
        }
        assert "id" in response_json
        job_id = response_json.pop("id")
        assert response_json == expected

        url = reverse("v1:reports-merge-jobs-detail", args=(job_id,))
        get_response = django_client.get(url)
        assert get_response.status_code == status.HTTP_200_OK

    def test_404_if_not_fingerprint_job(self, faker, django_client):
        """Test report job status only returns merge jobs."""
        source = Source.objects.create(
            name=faker.slug(),
            hosts=[faker.ipv4()],
            source_type="network",
            port=22,
        )
        scan_job, _ = create_scan_job(source, scan_type=ScanTask.SCAN_TYPE_INSPECT)

        url = reverse("v1:reports-merge-jobs-detail", args=(scan_job.id,))
        get_response = django_client.get(url)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

        scan_job.scan_type = ScanTask.SCAN_TYPE_FINGERPRINT
        scan_job.save()
        url = reverse("v1:reports-merge-jobs-detail", args=(scan_job.id,))
        get_response = django_client.get(url)
        assert get_response.status_code == status.HTTP_200_OK

    def test_create_report_merge_bad_url(self, django_client):
        """Create merge report job bad url."""
        get_response = django_client.post(
            reverse("v1:reports-merge-jobs-detail", args=(1,))
        )
        assert get_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_empty_request_body(self, django_client):
        """Test empty request body."""
        request_json = {}
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert response_json["report_type"] == messages.FC_REQUIRED_ATTRIBUTE

    def test_missing_sources(self, django_client):
        """Test missing sources attribute."""
        request_json = {"report_type": "details"}
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert response_json["sources"] == messages.FC_REQUIRED_ATTRIBUTE

    def test_empty_sources(self, django_client):
        """Test empty sources attribute."""
        request_json = {"report_type": "details", "sources": []}
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert response_json["sources"] == messages.FC_REQUIRED_ATTRIBUTE

    def test_source_missing_report_version(
        self, server_id, network_source, django_client
    ):
        """Test source missing report version."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                    "facts": [{"key": "value"}],
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["report_version"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_source_missing_name(self, django_client):
        """Test source is missing source_name."""
        request_json = {"report_type": "details", "sources": [{"foo": "abc"}]}
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["source_name"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_source_empty_name(self, django_client):
        """Test source has empty source_name."""
        request_json = {"report_type": "details", "sources": [{"source_name": ""}]}
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["source_name"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_source_name_not_string(self, server_id, network_source, django_client):
        """Test source has source_name that is not a string."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": 100,
                    "source_type": network_source.source_type,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["source_name"]
            == messages.FC_SOURCE_NAME_NOT_STR
        )

    def test_missing_source_type(self, server_id, network_source, django_client):
        """Test source_type is missing."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["source_type"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_empty_source_type(self, server_id, network_source, django_client):
        """Test source_type is empty."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_id": network_source.id,
                    "source_type": "",
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["source_type"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_invalid_source_type(self, server_id, network_source, django_client):
        """Test source_type has invalid_value."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": "abc",
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1

        valid_choices = ", ".join(DataSources.values)

        assert (
            response_json["invalid_sources"][0]["errors"]["source_type"]
            == messages.FC_MUST_BE_ONE_OF % valid_choices
        )

    def test_source_missing_facts(self, server_id, network_source, django_client):
        """Test source missing facts attr."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["facts"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    def test_source_empty_facts(self, server_id, network_source, django_client):
        """Test source has empty facts list."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": server_id,
                    "report_version": create_report_version(),
                    "source_name": network_source.name,
                    "source_type": network_source.source_type,
                    "facts": [],
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(
            request_json, django_client
        )
        assert len(response_json["valid_sources"]) == 0
        assert len(response_json["invalid_sources"]) == 1
        assert (
            response_json["invalid_sources"][0]["errors"]["facts"]
            == messages.FC_REQUIRED_ATTRIBUTE
        )

    ##############################################################
    # Test PUT Async Report Merge
    ##############################################################
    def merge_details_by_ids(self, data, django_client):
        """Call the create endpoint."""
        return django_client.put(reverse("v1:reports-merge-jobs"), json=data)

    def merge_details_by_ids_expect_201(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data, django_client)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def merge_details_by_ids_expect_400(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data, django_client)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        return response.json()

    def test_sync_merge_empty_body(self, django_client):
        """Test report merge by id with empty body."""
        data = None
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_REQUIRED]}

    def test_by_id_merge_empty_dict(self, django_client):
        """Test report merge by id with empty dict."""
        data = {}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_REQUIRED]}

    def test_by_id_merge_jobs_not_list(self, django_client):
        """Test report merge by id with not list."""
        data = {"reports": 5}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_LIST]}

    def test_by_id_merge_jobs_list_too_short(self, django_client):
        """Test report merge by id with list too short."""
        data = {"reports": [5]}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_TOO_SHORT]}

    def test_by_id_merge_jobs_list_empty(self, django_client):
        """Test report merge by id with an empty list."""
        data = {"reports": []}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_TOO_SHORT]}

    def test_by_id_merge_jobs_list_contains_string(self, django_client):
        """Test report merge by id with containing str."""
        data = {"reports": [5, "hello"]}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_INT]}

    def test_by_id_merge_jobs_list_contains_duplicates(self, django_client):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 5]}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_UNIQUE]}

    def test_by_id_merge_jobs_list_contains_invalid_job_ids(self, django_client):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 6]}
        json_response = self.merge_details_by_ids_expect_400(data, django_client)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_FOUND % "5, 6"]}

    def test_by_id_merge_jobs_success(self, server_id, network_source, django_client):
        """Test report merge by id jobs success."""
        url = reverse("v1:reports-list")
        sources1 = [
            {
                "server_id": server_id,
                "report_version": create_report_version(),
                "source_name": network_source.name,
                "source_type": network_source.source_type,
                "facts": [{"key1": "value1"}],
            }
        ]
        sources2 = [
            {
                "server_id": "abc",
                "report_version": create_report_version(),
                "source_name": "another_name",
                "source_type": "network",
                "facts": [{"key2": "value2"}],
            }
        ]
        request_json = {"report_type": "details", "sources": sources1}
        response = django_client.post(url, json=request_json)
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        assert response_json["sources"] == sources1
        report1_id = response_json["report_id"]

        request_json = {"report_type": "details", "sources": sources2}
        response = django_client.post(url, json=request_json)
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        assert response_json["sources"] == sources2
        report2_id = response_json["report_id"]

        data = {"reports": [report1_id, report2_id]}
        json_response = self.merge_details_by_ids_expect_201(data, django_client)
        expected = {
            "id": mock.ANY,
            "report_id": mock.ANY,
            "scan_type": "fingerprint",
            "status": "created",
            "status_message": "Job is created.",
        }

        assert json_response == expected
