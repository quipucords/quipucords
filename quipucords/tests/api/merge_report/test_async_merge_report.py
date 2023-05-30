"""Test the report API."""

import json
from unittest.mock import patch

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api import messages
from api.common.common_report import create_report_version
from api.models import Credential, ScanTask, ServerInformation, Source
from constants import DataSources
from tests.mixins import LoggedUserMixin
from tests.scanner.test_util import create_scan_job


def dummy_start():
    """Create a dummy method for testing."""


class AsyncMergeReports(LoggedUserMixin, TestCase):
    """Tests against the Deployment reports function."""

    def setUp(self):
        """Create test case setup."""
        management.call_command("flush", "--no-input")
        super().setUp()
        self.net_source = Source.objects.create(
            name="test_source", source_type=DataSources.NETWORK
        )

        self.net_cred = Credential.objects.create(
            name="net_cred1",
            cred_type=DataSources.NETWORK,
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.net_source.credentials.add(self.net_cred)

        self.net_source.hosts = ["1.2.3.4"]
        self.net_source.save()
        self.server_id = ServerInformation.create_or_retrieve_server_id()

    def merge_details_from_source(self, data):
        """Call the create endpoint."""
        url = "/api/v1/reports/merge/jobs/"
        return self.client.post(url, json.dumps(data), "application/json")

    def merge_details_from_source_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.merge_details_from_source(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def merge_details_from_source_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.merge_details_from_source(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    ##############################################################
    # Test Async Report Merge
    ##############################################################

    @patch("api.merge_report.view.start_scan", side_effect=dummy_start)
    def test_greenpath_create(self, start_scan):
        """Create report merge job object via API."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": [{"key": "value"}],
                }
            ],
        }

        response_json = self.merge_details_from_source_expect_201(request_json)

        expected = {
            "scan_type": "fingerprint",
            "status": "created",
            "status_message": "Job is created.",
        }
        self.assertIn("id", response_json)
        job_id = response_json.pop("id")
        self.assertEqual(response_json, expected)

        url = f"/api/v1/reports/merge/jobs/{job_id}/"
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_404_if_not_fingerprint_job(self):
        """Test report job status only returns merge jobs."""
        source = Source(
            name="source1",
            hosts=["1.2.3.4"],
            source_type="network",
            port=22,
        )
        source.save()
        scan_job, _ = create_scan_job(source, scan_type=ScanTask.SCAN_TYPE_INSPECT)

        url = f"/api/v1/reports/merge/jobs/{scan_job.id}/"
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

        scan_job.scan_type = ScanTask.SCAN_TYPE_FINGERPRINT
        scan_job.save()
        url = f"/api/v1/reports/merge/jobs/{scan_job.id}/"
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_create_report_merge_bad_url(self):
        """Create merge report job bad url."""
        url = "/api/v1/reports/merge/jobs/1/"
        get_response = self.client.post(url)
        self.assertEqual(get_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_empty_request_body(self):
        """Test empty request body."""
        request_json = {}
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(response_json["report_type"], messages.FC_REQUIRED_ATTRIBUTE)

    def test_missing_sources(self):
        """Test missing sources attribute."""
        request_json = {"report_type": "details"}
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(response_json["sources"], messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_sources(self):
        """Test empty sources attribute."""
        request_json = {"report_type": "details", "sources": []}
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(response_json["sources"], messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_missing_report_version(self):
        """Test source missing report version."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": [{"key": "value"}],
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["report_version"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_missing_name(self):
        """Test source is missing source_name."""
        request_json = {"report_type": "details", "sources": [{"foo": "abc"}]}
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_name"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_empty_name(self):
        """Test source has empty source_name."""
        request_json = {"report_type": "details", "sources": [{"source_name": ""}]}
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_name"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_name_not_string(self):
        """Test source has source_name that is not a string."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": 100,
                    "source_type": self.net_source.source_type,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_name"],
            messages.FC_SOURCE_NAME_NOT_STR,
        )

    def test_missing_source_type(self):
        """Test source_type is missing."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_type"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_empty_source_type(self):
        """Test source_type is empty."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_id": self.net_source.id,
                    "source_type": "",
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_type"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_invalid_source_type(self):
        """Test source_type has invalid_value."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": "abc",
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)

        valid_choices = ", ".join(DataSources.values)

        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_type"],
            messages.FC_MUST_BE_ONE_OF % valid_choices,
        )

    def test_source_missing_facts(self):
        """Test source missing facts attr."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["facts"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_empty_facts(self):
        """Test source has empty facts list."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": [],
                }
            ],
        }
        response_json = self.merge_details_from_source_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["facts"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    ##############################################################
    # Test PUT Async Report Merge
    ##############################################################
    def merge_details_by_ids(self, data):
        """Call the create endpoint."""
        url = "/api/v1/reports/merge/jobs/"
        return self.client.put(url, json.dumps(data), "application/json")

    def merge_details_by_ids_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def merge_details_by_ids_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    def test_sync_merge_empty_body(self):
        """Test report merge by id with empty body."""
        data = None
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_REQUIRED]})

    def test_by_id_merge_empty_dict(self):
        """Test report merge by id with empty dict."""
        data = {}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_REQUIRED]})

    def test_by_id_merge_jobs_not_list(self):
        """Test report merge by id with not list."""
        data = {"reports": 5}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_NOT_LIST]})

    def test_by_id_merge_jobs_list_too_short(self):
        """Test report merge by id with list too short."""
        data = {"reports": [5]}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_TOO_SHORT]})

    def test_by_id_merge_jobs_list_contains_string(self):
        """Test report merge by id with containing str."""
        data = {"reports": [5, "hello"]}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_NOT_INT]})

    def test_by_id_merge_jobs_list_contains_duplicates(self):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 5]}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(json_response, {"reports": [messages.REPORT_MERGE_NOT_UNIQUE]})

    def test_by_id_merge_jobs_list_contains_invalid_job_ids(self):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 6]}
        json_response = self.merge_details_by_ids_expect_400(data)
        self.assertEqual(
            json_response, {"reports": [messages.REPORT_MERGE_NOT_FOUND % "5, 6"]}
        )

    @patch("api.merge_report.view.start_scan", side_effect=dummy_start)
    def test_by_id_merge_jobs_success(self, mock_dummy_start):
        """Test report merge by id jobs success."""
        url = reverse("reports-list")
        sources1 = [
            {
                "server_id": self.server_id,
                "report_version": create_report_version(),
                "source_name": self.net_source.name,
                "source_type": self.net_source.source_type,
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
        response = self.client.post(url, json.dumps(request_json), "application/json")
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(response_json["sources"], sources1)
        report1_id = response_json["report_id"]

        request_json = {"report_type": "details", "sources": sources2}
        response = self.client.post(url, json.dumps(request_json), "application/json")
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(response_json["sources"], sources2)
        report2_id = response_json["report_id"]

        data = {"reports": [report1_id, report2_id]}
        json_response = self.merge_details_by_ids_expect_201(data)
        expected = {
            "id": 3,
            "scan_type": "fingerprint",
            "status": "created",
            "status_message": "Job is created.",
        }

        self.assertEqual(json_response, expected)
