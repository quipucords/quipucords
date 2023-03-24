"""Test the report API."""

import copy
import json
import tarfile

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.common.common_report import create_report_version
from api.common.report_json_gzip_renderer import ReportJsonGzipRenderer
from api.details_report.csv_renderer import DetailsCSVRenderer
from api.models import Credential, DetailsReport, ServerInformation, Source
from constants import DataSources


class MockRequest:
    """Mock a request object for the renderer."""

    def __init__(self, mask_rep=False):
        """Initialize a fake request object."""
        self.query_params = {"mask": mask_rep}


class DetailReportTest(TestCase):
    """Tests against the Detail reports function."""

    def setUp(self):
        """Create test case setup."""
        management.call_command("flush", "--no-input")
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
        self.report_version = create_report_version()
        self.mock_req = MockRequest()
        self.mock_renderer_context = {"request": self.mock_req}

    def tearDown(self):
        """Create test case tearDown."""

    def create(self, data):
        """Call the create endpoint."""
        url = reverse("reports-list")
        return self.client.post(url, json.dumps(data), "application/json")

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def retrieve_expect_200(self, identifier, query_param=""):
        """Create a source, return the response as a dict."""
        url = "/api/v1/reports/" + str(identifier) + "/details/" + query_param
        response = self.client.get(url)

        if response.status_code != status.HTTP_200_OK:
            print("Failure cause: ")
            print(response.json())
        assert response.status_code == status.HTTP_200_OK
        return response.json()

    def test_get_details_report_404(self):
        """Fail to get a report for missing collection."""
        url = "/api/v1/reports/24/details/"

        # Query API
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    ##############################################################
    # Test details endpoint
    ##############################################################
    def test_details(self):
        """Get details for a report via API."""
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
        identifier = response_json["report_id"]
        response_json = self.retrieve_expect_200(identifier)
        assert response_json["report_id"] == identifier

    def test_details_masked(self):
        """Get details report with masked values for a report via API."""
        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": [
                        {
                            "ip_addresses": ["1.2.3.4"],
                            "mac_addresses": ["1.2.3.5", "2.4.5.6"],
                            "uname_hostname": "foo",
                            "vm.name": "foo",
                        }
                    ],
                }
            ],
        }

        response_json = self.create_expect_201(request_json)
        identifier = response_json["report_id"]
        response_json = self.retrieve_expect_200(identifier, query_param="?mask=True")
        assert response_json["report_id"] == identifier
        # assert the ips/macs/hostname is masked
        source_to_check = response_json.get("sources")[0]
        facts = source_to_check.get("facts")
        expected_facts = [
            {
                "ip_addresses": ["-7334718598697473719"],
                "mac_addresses": ["-7048634151319043688", "-3493454847440916718"],
                "uname_hostname": "-2457967226571033580",
                "vm.name": "-2457967226571033580",
            }
        ]
        assert facts == expected_facts
        # test bad query param
        url = "/api/v1/reports/" + str(identifier) + "/details/?mask=foo"
        # Query API
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    ##############################################################
    # Test CSV Renderer
    ##############################################################

    def test_csv_renderer(self):  # pylint:disable=too-many-statements
        """Test DetailsCSVRenderer."""
        renderer = DetailsCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json, renderer_context=self.mock_renderer_context)
        assert value is None

        # Test doesn't exist
        test_json = {"id": 42}
        value = renderer.render(test_json, renderer_context=self.mock_renderer_context)
        assert value is None

        request_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": [
                        {
                            "ip_addresses": ["1.2.3.4"],
                            "mac_addresses": ["1.2.3.5", "2.4.5.6"],
                            "uname_hostname": "foo",
                            "vm.name": "foo",
                        }
                    ],
                }
            ],
        }

        response_json = self.create_expect_201(request_json)
        test_json = copy.deepcopy(response_json)
        csv_result = renderer.render(
            test_json, renderer_context=self.mock_renderer_context
        )
        expected = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"1,details,{self.report_version},{test_json.get('report_platform_id')},"
            "1\r\n\r\n\r\n"
            "Source\r\n"
            "Server Identifier,Source Name,Source Type\r\n"
            f"{self.server_id},test_source,network\r\n"
            "Facts\r\n"
            "ip_addresses,mac_addresses,uname_hostname,vm.name\r\n"
            "[1.2.3.4],[1.2.3.5;2.4.5.6],foo,foo\r\n\r\n\r\n"
        )
        assert csv_result == expected

        # Test cached works too
        test_json = copy.deepcopy(response_json)
        test_json["sources"][0]["facts"] = []
        csv_result = renderer.render(
            test_json, renderer_context=self.mock_renderer_context
        )
        # These would be different if not cached
        assert csv_result == expected

        # Clear cache
        details_report = DetailsReport.objects.get(report_id=response_json["report_id"])
        details_report.cached_csv = None
        details_report.save()

        # Test with hashing
        test_json["sources"][0]["facts"] = [
            {
                "ip_addresses": [str(hash("1.2.3.4"))],
                "mac_addresses": [str(hash("1.2.3.5")), str(hash("2.4.5.6"))],
                "uname_hostname": str(hash("foo")),
                "vm.name": str(hash("foo")),
            }
        ]
        new_mock_req = MockRequest(mask_rep=True)
        new_renderer = {"request": new_mock_req}
        csv_result = renderer.render(test_json, renderer_context=new_renderer)
        expected = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"1,details,{self.report_version},{test_json.get('report_platform_id')},"
            "1\r\n\r\n\r\n"
            "Source\r\n"
            "Server Identifier,Source Name,Source Type\r\n"
            f"{self.server_id},test_source,network\r\n"
            "Facts\r\n"
            "ip_addresses,mac_addresses,uname_hostname,vm.name\r\n"
            "[-7334718598697473719],[-7048634151319043688;-3493454847440916718],"
            "-2457967226571033580,-2457967226571033580\r\n\r\n\r\n"
        )
        assert csv_result == expected

        # Test cached works too for hashed
        test_json = copy.deepcopy(response_json)
        test_json["sources"][0]["facts"] = []
        csv_result = renderer.render(test_json, renderer_context=new_renderer)
        # These would be different if not cached
        assert csv_result == expected

        # Clear cache
        details_report = DetailsReport.objects.get(report_id=response_json["report_id"])
        details_report.cached_csv = None
        details_report.save()

        # Clear cache
        details_report = DetailsReport.objects.get(report_id=response_json["report_id"])
        details_report.cached_csv = None
        details_report.save()

        # Remove sources
        test_json = copy.deepcopy(response_json)
        test_json["sources"] = None
        csv_result = renderer.render(
            test_json, renderer_context=self.mock_renderer_context
        )
        expected = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"1,details,{self.report_version},{test_json.get('report_platform_id')},"
            "0\r\n"
        )
        assert csv_result == expected

        # Clear cache
        details_report = DetailsReport.objects.get(id=response_json["report_id"])
        details_report.cached_csv = None
        details_report.save()

        # Remove sources
        test_json = copy.deepcopy(response_json)
        test_json["sources"] = []
        csv_result = renderer.render(
            test_json, renderer_context=self.mock_renderer_context
        )
        expected = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"1,details,{self.report_version},{test_json.get('report_platform_id')},"
            "0\r\n\r\n\r\n"
        )
        assert csv_result == expected

        # Clear cache
        details_report = DetailsReport.objects.get(report_id=response_json["report_id"])
        details_report.cached_csv = None
        details_report.save()

        # Remove facts
        test_json = copy.deepcopy(response_json)
        test_json["sources"][0]["facts"] = []
        csv_result = renderer.render(
            test_json, renderer_context=self.mock_renderer_context
        )
        expected = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"1,details,{self.report_version},{test_json.get('report_platform_id')},"
            "1\r\n\r\n\r\n"
            "Source\r\n"
            "Server Identifier,Source Name,Source Type\r\n"
            f"{self.server_id},test_source,network\r\n"
            "Facts\r\n\r\n"
        )
        assert csv_result == expected

    ##############################################################
    # Test Json Gzip Render
    ##############################################################
    def test_json_gzip_renderer(self):
        """Test ReportJsonGzipRenderer for details."""
        renderer = ReportJsonGzipRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        assert value is None

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

        report_dict = self.create_expect_201(request_json)

        # Test that the data in the subfile equals the report_dict
        tar_gz_result = renderer.render(report_dict)
        with tarfile.open(fileobj=tar_gz_result) as tar:
            json_file = tar.getmembers()[0]
            tar_info = tar.extractfile(json_file)
            tar_dict_data = json.loads(tar_info.read().decode())
            assert tar_dict_data == report_dict
