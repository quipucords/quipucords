"""Test the reports API."""

import csv
import hashlib
import json
import logging
import sys
import tarfile
from io import BytesIO

import pytest
from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.common.common_report import create_report_version
from api.deployments_report.model import DeploymentsReport
from api.models import Credential, ServerInformation, Source
from api.reports.reports_gzip_renderer import ReportsGzipRenderer
from constants import SCAN_JOB_LOG, DataSources
from tests.api.details_report.test_details_report import MockRequest
from tests.factories import DeploymentReportFactory
from tests.mixins import LoggedUserMixin


class ReportsTest(LoggedUserMixin, TestCase):
    """Tests against the Reports function."""

    def setUp(self):
        """Create test case setup."""
        management.call_command("flush", "--no-input")
        super().setUp()
        self.maxDiff = None  # more verbose test failure results
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
        self.details_json = None
        self.deployments_json = None
        self.mock_req = MockRequest()
        self.mock_renderer_context = {"request": self.mock_req}

    def tearDown(self):
        """Create test case tearDown."""

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
        details_json = response.json()
        self.details_json = details_json
        return details_json

    def generate_fingerprints(self, os_name="RHEL", os_versions=None):
        """Create a DetailsReport for test."""
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
                "connection_uuid": "834c8f3b-5015-4156-bfb7-286d3ffe11b4",
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
                "ifconfig_ip_addresses": ["1.2.3.4"],
            }
            facts.append(fact_json)
        details_report = self.create_details_report_expect_201(fc_json)
        return details_report

    def retrieve_expect_200_details(self, identifier, query_param=""):
        """Create a source, return the response as a dict."""
        url = "/api/v1/reports/" + str(identifier) + "/details/" + query_param
        response = self.client.get(url)

        if response.status_code != status.HTTP_200_OK:
            print("Failure cause: ")
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def create_reports_dict(self, query_params=""):
        """Create a deployments report."""
        url = "/api/v1/reports/1/deployments/" + query_params
        self.generate_fingerprints(os_versions=["7.4", "7.4", "7.5"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.deployments_json = report
        self.details_json = self.retrieve_expect_200_details(1, query_params)

        reports_dict = {}
        reports_dict["report_id"] = 1
        reports_dict["details_json"] = self.details_json
        reports_dict["deployments_json"] = self.deployments_json
        return reports_dict

    def test_reports_gzip_renderer(self):
        """Get a tar.gz return for report_id via API."""
        reports_dict = self.create_reports_dict()
        deployments_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID\r\n"
            f"1,deployments,{self.report_version},{reports_dict.get('deployments_json').get('report_platform_id')}\r\n"  # noqa: E501
            "\r\n"
            "\r\n"
            "System Fingerprints:\r\n"
            "architecture,bios_uuid,cloud_provider,cpu_core_count,cpu_count,cpu_hyperthreading,cpu_socket_count,detection-ansible,detection-network,detection-openshift,detection-satellite,detection-vcenter,entitlements,etc_machine_id,infrastructure_type,insights_client_id,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,jboss web server,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_addons,system_creation_date,system_last_checkin_date,system_memory_bytes,system_role,system_service_level_agreement,system_usage_type,system_user_count,user_login_history,virtual_host_name,virtual_host_uuid,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host_core_count,vm_host_socket_count,vm_state,vm_uuid\r\n"  # noqa: E501
            ",,,2,2,,2,False,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,False,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,False,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.5,7.5,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            "\r\n"
        )

        details_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n1,details,%s,%s,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\nconnection_host,connection_port,connection_uuid,cpu_core_count,cpu_core_per_socket,cpu_count,cpu_hyperthreading,cpu_siblings,cpu_socket_count,date_anaconda_log,date_yum_history,etc_release_name,etc_release_release,etc_release_version,ifconfig_ip_addresses,uname_hostname,virt_num_guests,virt_num_running_guests,virt_type,virt_virt,virt_what_type\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.5,7.5,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n\r\n\r\n"  # noqa: E501
            % (
                self.report_version,
                reports_dict.get("details_json").get("report_platform_id"),
                self.server_id,
            )
        )

        renderer = ReportsGzipRenderer()
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=self.mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        with tarfile.open(fileobj=tar_gz_result) as tarball:
            self.check_tarball(deployments_csv, details_csv, tarball)

    def check_tarball(
        self, deployments_csv: str, details_csv: str, tar: tarfile.TarFile
    ):
        """
        Check report tarball content.

        :param deployments_csv: CSV for deployments report
        :param details_csv: CSV for details report
        :param tar: Tar object to examine for equality
        """
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith("csv"):
                if "details" in file_contents:
                    self.assertEqual(
                        self.parse_csv(file_contents), self.parse_csv(details_csv)
                    )
                elif "deployments" in file_contents:
                    self.assertEqual(
                        self.parse_csv(file_contents), self.parse_csv(deployments_csv)
                    )
                else:
                    sys.exit("Could not identify .csv return.")
            elif filenames[idx].endswith("json"):
                tar_json = json.loads(file_contents)
                tar_json_type = tar_json.get("report_type")
                if tar_json_type == "details":
                    self.assertEqual(tar_json, self.details_json)
                elif tar_json_type == "deployments":
                    self.assertEqual(tar_json, self.deployments_json)
                else:
                    sys.exit("Could not identify .json return")

    def parse_csv(self, file_contents: str):
        """Parse a string formatted as csv."""
        return list(csv.reader(file_contents.splitlines()))

    def test_parse_csv(self):
        """Test parse_csv utility."""
        self.assertEqual(self.parse_csv("1,2,3\na,b,c"), [list("123"), list("abc")])

    def test_sha256sum(self):
        """Ensure SHA256SUM hashes are correct."""
        reports_dict = self.create_reports_dict()
        renderer = ReportsGzipRenderer()
        mock_req = MockRequest()
        mock_renderer_context = {"request": mock_req}
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)
        files = tar.getmembers()
        # ignore folder name
        filenames = [file.rsplit("/", 1)[1] for file in tar.getnames()]
        # tar.getnames() always returns same order as tar.getmembers()
        filename_to_file = dict(zip(filenames, files))
        shasum_content = tar.extractfile(filename_to_file["SHA256SUM"]).read().decode()
        # map calculated hashes for future comparison
        file2hash = {}
        for line in shasum_content.splitlines():
            calculated_hash, hashed_filename = line.split()
            file2hash[hashed_filename] = calculated_hash

        expected_hashed_filenames = {
            "details.json",
            "deployments.json",
            "details.csv",
            "deployments.csv",
        }
        self.assertEqual(set(file2hash), expected_hashed_filenames)
        # recalculate hashes
        new_file2hash = {}
        for hashed_filename, calculated_hash in file2hash.items():
            file = filename_to_file[hashed_filename]
            file_contents = tar.extractfile(file).read()
            new_hash = hashlib.sha256(file_contents).hexdigest()
            new_file2hash[hashed_filename] = new_hash
        self.assertEqual(new_file2hash, file2hash, "SHA256SUM content is incorrect")


def test_report_without_logs(django_client, caplog):
    """Explicitly test report without logs."""
    caplog.set_level(logging.WARNING)
    deployment = DeploymentReportFactory.create()
    report_id = deployment.report.id
    response = django_client.get(f"/api/v1/reports/{report_id}/")
    assert response.ok, response.text
    assert f"No logs were found for report_id={report_id}" in caplog.messages
    expected_files = {
        f"report_id_{report_id}/{fname}"
        for fname in [
            "SHA256SUM",
            "deployments.csv",
            "deployments.json",
            "details.csv",
            "details.json",
        ]
    }
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        assert set(tarball.getnames()) == expected_files


@pytest.fixture
def deployment_with_logs(settings, faker):
    """Return a completed DeploymentReport instance that has associate scan job logs."""
    deployments_report: DeploymentsReport = DeploymentReportFactory.create()
    scan_job_id = deployments_report.report.scanjob.id
    log_file = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
        scan_job_id=scan_job_id, output_type="test"
    )
    log_file.write_text(faker.paragraph())
    return deployments_report


def test_report_with_logs(django_client, deployment_with_logs):
    """Test if scan job logs are included in tarball when present."""
    report = deployment_with_logs.report
    scan_job_id = report.scanjob.id
    response = django_client.get(f"/api/v1/reports/{report.id}/")
    assert response.ok, response.text
    expected_files = {
        f"report_id_{report.id}/{fname}"
        for fname in [
            "SHA256SUM",
            "deployments.csv",
            "deployments.json",
            "details.csv",
            "details.json",
            f"scan-job-{scan_job_id}-test.txt",
        ]
    }
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        assert set(tarball.getnames()) == expected_files
