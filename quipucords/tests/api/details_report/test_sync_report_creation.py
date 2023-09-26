"""Test the fact API."""

import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api import messages
from api.common.common_report import create_report_version
from api.models import Credential, Report, ServerInformation, Source
from constants import DataSources
from tests.mixins import LoggedUserMixin


class DetailsReportTest(LoggedUserMixin, TestCase):
    """Tests against the Report model and view set."""

    def setUp(self):
        """Create test case setup."""
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

    def create(self, data):
        """Call the create endpoint."""
        url = reverse("reports-list")
        return self.client.post(url, json.dumps(data), "application/json")

    def create_expect_400(self, data, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_json = response.json()
        if expected_response:
            self.assertEqual(response_json, expected_response)
        return response_json

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    ################################################################
    # Test Model Create
    ################################################################
    def test_greenpath_create(self):
        """Create fact collection object via API."""
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

        response_json = self.create_expect_201(request_json)
        self.assertEqual(response_json["sources"], request_json["sources"])
        self.assertEqual(Report.objects.count(), 1)

    def test_empty_request_body(self):
        """Test empty request body."""
        request_json = {}
        response_json = self.create_expect_400(request_json)
        self.assertEqual(response_json["report_type"], messages.FC_REQUIRED_ATTRIBUTE)

    def test_missing_sources(self):
        """Test missing sources attribute."""
        request_json = {"report_type": "details"}
        response_json = self.create_expect_400(request_json)
        self.assertEqual(response_json["sources"], messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_sources(self):
        """Test empty sources attribute."""
        request_json = {"report_type": "details", "sources": []}
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["report_version"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_missing_name(self):
        """Test source is missing source_name."""
        request_json = {"report_type": "details", "sources": [{"foo": "abc"}]}
        response_json = self.create_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["source_name"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )

    def test_source_empty_name(self):
        """Test source has empty source_name."""
        request_json = {"report_type": "details", "sources": [{"source_name": ""}]}
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
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
        response_json = self.create_expect_400(request_json)
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
                    "source_name": self.net_source.name,
                    "report_version": create_report_version(),
                    "source_type": self.net_source.source_type,
                    "facts": [],
                }
            ],
        }
        response_json = self.create_expect_400(request_json)
        self.assertEqual(len(response_json["valid_sources"]), 0)
        self.assertEqual(len(response_json["invalid_sources"]), 1)
        self.assertEqual(
            response_json["invalid_sources"][0]["errors"]["facts"],
            messages.FC_REQUIRED_ATTRIBUTE,
        )
