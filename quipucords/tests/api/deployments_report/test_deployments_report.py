"""Test the report API."""

import json
import tarfile
import uuid

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.common.common_report import create_report_version
from api.common.report_json_gzip_renderer import ReportJsonGzipRenderer
from api.deployments_report.csv_renderer import DeploymentCSVRenderer
from api.deployments_report.util import sanitize_row
from api.models import Credential, ServerInformation, Source
from constants import DataSources
from tests.api.details_report.test_details_report import MockRequest
from tests.mixins import LoggedUserMixin

EXPECTED_NUMBER_OF_FINGERPRINTS = 38


class DeploymentReportTest(LoggedUserMixin, TestCase):
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
        self.report_version = create_report_version()
        self.mock_request = MockRequest()
        self.mock_renderer_context = {"request": self.mock_request}

    def create_details_report(self, data):
        """Call the create endpoint."""
        url = reverse("reports-list")
        return self.client.post(url, json.dumps(data), "application/json")

    def create_details_report_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_details_report(data)
        if response.status_code != status.HTTP_201_CREATED:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def create_details_report_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_details_report(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    def generate_fingerprints(self, os_name="RHEL", os_versions=None):
        """Create a Report and DeploymentsReport for test."""
        facts = []
        fc_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": facts,
                }
            ],
        }

        if os_versions is None:
            os_versions = ["7.3", "7.4"]

        for version in os_versions:
            release = f"{os_name} {version}"
            fact_json = {
                "connection_host": "1.2.3.4",
                "connection_port": 22,
                "connection_uuid": str(uuid.uuid4()),
                "cpu_count": 2,
                "cpu_core_per_socket": 1,
                "cpu_siblings": 1,
                "cpu_hyperthreading": False,
                "cpu_socket_count": 2,
                "cpu_core_count": 2,
                "date_anaconda_log": "2017-07-18",
                "date_yum_history": "2017-07-18",
                "etc_release_name": os_name,
                "etc_release_version": version,
                "etc_release_release": release,
                "uname_hostname": "1.2.3.4",
                "virt_virt": "virt-guest",
                "virt_type": "vmware",
                "virt_num_guests": 1,
                "virt_num_running_guests": 1,
                "virt_what_type": "vt",
            }
            facts.append(fact_json)
        report = self.create_details_report_expect_201(fc_json)
        return report

    def test_get_details_report_group_report(self):
        """Get a specific group count report."""
        url = "/api/v1/reports/1/deployments/"

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(os_versions=["7.4", "7.4", "7.5"])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(
            len(report["system_fingerprints"][0].keys()),
            EXPECTED_NUMBER_OF_FINGERPRINTS,
        )

    def test_get_deployments_report_404(self):
        """Fail to get a report for missing collection."""
        url = "/api/v1/reports/2/deployments/"

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(os_versions=["7.4", "7.4", "7.5"])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_bad_deployment_report(self):
        """Test case where Report exists but no fingerprint."""
        url = "/api/v1/reports/1/deployments/"

        # Create a system fingerprint via collection receiver
        facts = []
        fc_json = {
            "report_type": "details",
            "sources": [
                {
                    "server_id": self.server_id,
                    "report_version": create_report_version(),
                    "source_name": self.net_source.name,
                    "source_type": self.net_source.source_type,
                    "facts": facts,
                }
            ],
        }

        fact_json = {
            "cpu_core_count": "cat",
        }
        facts.append(fact_json)
        self.create_details_report_expect_400(fc_json)

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    def test_get_details_report_bad_id(self):
        """Fail to get a report for missing collection."""
        url = "/api/v1/reports/string/deployments/"

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ##############################################################
    # Test CSV Renderer
    ##############################################################

    def test_sanitize_row(self):
        """Test sanitize_row function."""
        self.assertEqual(
            sanitize_row(["data", None, "data,data"]), ["data", None, "data;data"]
        )

    def test_csv_renderer(self):
        """Test DeploymentCSVRenderer."""
        renderer = DeploymentCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json, renderer_context=self.mock_renderer_context)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {"id": 42}
        value = renderer.render(test_json, renderer_context=self.mock_renderer_context)
        self.assertIsNone(value)

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(os_versions=["7.4", "7.4", "7.5"])
        url = "/api/v1/reports/1/deployments/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()

        csv_result = renderer.render(
            report, renderer_context=self.mock_renderer_context
        )
        # skip csv headers and last line
        csv_lines = csv_result.splitlines()[5:-1]

        data_rows = [
            "architecture,bios_uuid,cloud_provider,cpu_core_count,cpu_count,cpu_hyperthreading,cpu_socket_count,detection-ansible,detection-network,detection-openshift,detection-satellite,detection-vcenter,entitlements,etc_machine_id,infrastructure_type,insights_client_id,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,jboss web server,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_addons,system_creation_date,system_last_checkin_date,system_memory_bytes,system_role,system_service_level_agreement,system_usage_type,system_user_count,user_login_history,virtual_host_name,virtual_host_uuid,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host_core_count,vm_host_socket_count,vm_state,vm_uuid",  # noqa: E501
            ",,,2,2,,2,False,True,False,False,False,,,virtualized,,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,",  # noqa: E501
            ",,,2,2,False,2,False,True,False,False,False,,,virtualized,,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,",  # noqa: E501
            ",,,2,2,False,2,False,True,False,False,False,,,virtualized,,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.5,7.5,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,",  # noqa: E501
        ]
        assert len(csv_lines) == len(data_rows)
        for expected_row, csv_row in zip(data_rows, csv_lines):
            assert expected_row.split(",") == csv_row.split(",")

    ##############################################################
    # Test Json Gzip Render
    ##############################################################
    def test_json_gzip_renderer(self):
        """Test ReportJsonGzipRenderer for deployments."""
        renderer = ReportJsonGzipRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {"id": 42}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(os_versions=["7.4", "7.4", "7.5"])
        url = "/api/v1/reports/1/deployments/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_dict = response.json()

        # Test that the data in the subfile equals the report_dict
        tar_gz_result = renderer.render(report_dict)
        with tarfile.open(fileobj=tar_gz_result) as tar:
            json_file = tar.getmembers()[0]
            tar_info = tar.extractfile(json_file)
            tar_dict_data = json.loads(tar_info.read().decode())
            self.assertEqual(tar_dict_data, report_dict)
