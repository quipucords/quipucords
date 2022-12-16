#
# Copyright (c) 2018-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the reports API."""

import json
import sys
import tarfile
from pathlib import Path

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.serializers import ValidationError

from api.common.common_report import create_report_version
from api.details_report.tests_details_report import MockRequest
from api.models import Credential, ServerInformation, Source
from api.reports.reports_gzip_renderer import ReportsGzipRenderer, create_hash


class ReportsTest(TestCase):
    """Tests against the Reports function."""

    # pylint: disable=invalid-name,too-many-instance-attributes
    def setUp(self):
        """Create test case setup."""
        management.call_command("flush", "--no-input")
        self.net_source = Source.objects.create(
            name="test_source", source_type=Source.NETWORK_SOURCE_TYPE
        )

        self.net_cred = Credential.objects.create(
            name="net_cred1",
            cred_type=Credential.NETWORK_CRED_TYPE,
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.net_source.credentials.add(self.net_cred)

        self.net_source.hosts = '["1.2.3.4"]'
        self.net_source.save()
        self.server_id = ServerInformation.create_or_retreive_server_id()
        self.report_version = create_report_version()
        self.details_json = None
        self.deployments_json = None
        self.mock_req = MockRequest()
        self.mock_renderer_context = {"request": self.mock_req}
        self.test_data_path = Path(__file__).parent / "test_data"

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
            release = "{} {}".format(os_name, version)
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

        reports_dict = dict()
        reports_dict["report_id"] = 1
        reports_dict["details_json"] = self.details_json
        reports_dict["deployments_json"] = self.deployments_json
        return reports_dict

    # pylint: disable=too-many-locals, too-many-branches
    def test_reports_gzip_renderer(self):
        """Get a tar.gz return for report_id via API."""
        reports_dict = self.create_reports_dict()
        deployments_csv_path = self.test_data_path / "deployments.csv"
        details_csv_path = self.test_data_path / "details.csv"
        deployments_csv = deployments_csv_path.read_text().format(
            report_version=self.report_version,
            report_platform_id=reports_dict["deployments_json"]["report_platform_id"],
        )
        details_csv = details_csv_path.read_text().format(
            report_version=self.report_version,
            report_platform_id=reports_dict["details_json"]["report_platform_id"],
            server_id=self.server_id,
        )

        renderer = ReportsGzipRenderer()
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=self.mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith("csv"):
                if "details" in file_contents:
                    assert file_contents.splitlines() == details_csv.splitlines()
                elif "deployments" in file_contents:
                    assert file_contents.splitlines() == deployments_csv.splitlines()
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
            else:
                # verify the hashes
                name_to_hash = {
                    "details.json": create_hash(self.details_json, "json"),
                    "deployments.json": create_hash(self.deployments_json, "json"),
                    "details.csv": create_hash(details_csv, "csv"),
                    "deployments.csv": create_hash(deployments_csv, "csv"),
                }
                for name, rep_hash in name_to_hash.items():
                    for line in file_contents:
                        if name in line:
                            self.assertIn(rep_hash, line)

    # pylint: disable=too-many-locals, too-many-branches
    def test_reports_gzip_renderer_masked(self):
        """Get a tar.gz return for report_id via API with masked values."""
        reports_dict = self.create_reports_dict(query_params="?mask=True")

        deployments_csv_path = self.test_data_path / "deployments_masked.csv"
        details_csv_path = self.test_data_path / "details_masked.csv"
        deployments_csv = deployments_csv_path.read_text().format(
            report_version=self.report_version,
            report_platform_id=reports_dict["deployments_json"]["report_platform_id"],
        )
        details_csv = details_csv_path.read_text().format(
            report_version=self.report_version,
            report_platform_id=reports_dict["details_json"]["report_platform_id"],
            server_id=self.server_id,
        )
        renderer = ReportsGzipRenderer()
        mock_req = MockRequest(mask_rep=True)
        mock_renderer_context = {"request": mock_req}
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith("csv"):
                if "details" in file_contents:
                    assert file_contents.splitlines() == details_csv.splitlines()
                elif "deployments" in file_contents:
                    assert file_contents.splitlines() == deployments_csv.splitlines()
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
            else:
                # verify the hashes
                name_to_hash = {
                    "details.json": create_hash(self.details_json, "json"),
                    "deployments.json": create_hash(self.deployments_json, "json"),
                    "details.csv": create_hash(details_csv, "csv"),
                    "deployments.csv": create_hash(deployments_csv, "csv"),
                }
                for name, rep_hash in name_to_hash.items():
                    for line in file_contents:
                        if name in line:
                            self.assertIn(rep_hash, line)

    def test_reports_gzip_renderer_masked_bad_req(self):
        """Get a tar.gz return for report_id via API with a bad query param."""
        reports_dict = self.create_reports_dict(query_params="?mask=True")
        renderer = ReportsGzipRenderer()
        mock_req = MockRequest(mask_rep="foo")
        mock_renderer_context = {"request": mock_req}
        with self.assertRaises(ValidationError):
            tar_gz_result = renderer.render(
                reports_dict, renderer_context=mock_renderer_context
            )
            self.assertEqual(tar_gz_result, None)
