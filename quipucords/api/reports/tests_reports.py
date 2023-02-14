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

import hashlib
import json
import sys
import tarfile

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.serializers import ValidationError

from api.common.common_report import create_report_version
from api.details_report.tests_details_report import MockRequest
from api.models import Credential, ServerInformation, Source
from api.reports.reports_gzip_renderer import ReportsGzipRenderer


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

    # pylint: disable=too-many-locals, too-many-branches
    def test_reports_gzip_renderer(self):
        """Get a tar.gz return for report_id via API."""
        # pylint: disable=line-too-long
        reports_dict = self.create_reports_dict()
        deployments_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID\r\n"
            f"1,deployments,{self.report_version},{reports_dict.get('deployments_json').get('report_platform_id')}\r\n"  # noqa: E501
            "\r\n"
            "\r\n"
            "System Fingerprints:\r\n"
            "architecture,bios_uuid,cloud_provider,cpu_core_count,cpu_count,cpu_hyperthreading,cpu_socket_count,detection-network,detection-openshift,detection-satellite,detection-vcenter,entitlements,etc_machine_id,infrastructure_type,insights_client_id,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,jboss web server,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_addons,system_creation_date,system_last_checkin_date,system_memory_bytes,system_role,system_service_level_agreement,system_usage_type,system_user_count,user_login_history,virtual_host_name,virtual_host_uuid,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host_core_count,vm_host_socket_count,vm_state,vm_uuid\r\n"  # noqa: E501
            ",,,2,2,,2,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,True,False,False,False,,,virtualized,,[1.2.3.4],,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.5,7.5,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            "\r\n"
        )

        # pylint: disable=line-too-long, consider-using-f-string
        details_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n1,details,%s,%s,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\nconnection_host,connection_port,connection_uuid,cpu_core_count,cpu_core_per_socket,cpu_count,cpu_hyperthreading,cpu_siblings,cpu_socket_count,date_anaconda_log,date_yum_history,etc_release_name,etc_release_release,etc_release_version,ifconfig_ip_addresses,uname_hostname,virt_num_guests,virt_num_running_guests,virt_type,virt_virt,virt_what_type\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.5,7.5,[1.2.3.4],1.2.3.4,1,1,vmware,virt-guest,vt\r\n\r\n\r\n"  # noqa: E501
            % (
                self.report_version,
                reports_dict.get("details_json").get("report_platform_id"),
                self.server_id,
            )
        )  # noqa

        renderer = ReportsGzipRenderer()
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=self.mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)  # pylint: disable=consider-using-with
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith("csv"):
                if "details" in file_contents:
                    assert file_contents == details_csv
                elif "deployments" in file_contents:
                    assert file_contents == deployments_csv
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

    # pylint: disable=too-many-locals, too-many-branches
    def test_reports_gzip_renderer_masked(self):
        """Get a tar.gz return for report_id via API with masked values."""
        # pylint: disable=line-too-long
        reports_dict = self.create_reports_dict(query_params="?mask=True")
        deployments_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID\r\n"
            f"1,deployments,{self.report_version},{reports_dict.get('deployments_json').get('report_platform_id')}\r\n"  # noqa: E501
            "\r\n"
            "\r\n"
            "System Fingerprints:\r\n"
            "architecture,bios_uuid,cloud_provider,cpu_core_count,cpu_count,cpu_hyperthreading,cpu_socket_count,detection-network,detection-openshift,detection-satellite,detection-vcenter,entitlements,etc_machine_id,infrastructure_type,insights_client_id,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,jboss web server,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_addons,system_creation_date,system_last_checkin_date,system_memory_bytes,system_role,system_service_level_agreement,system_usage_type,system_user_count,user_login_history,virtual_host_name,virtual_host_uuid,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host_core_count,vm_host_socket_count,vm_state,vm_uuid\r\n"  # noqa: E501
            ",,,2,2,,2,True,False,False,False,,,virtualized,,[-7334718598697473719],,absent,absent,absent,absent,,-7334718598697473719,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,True,False,False,False,,,virtualized,,[-7334718598697473719],,absent,absent,absent,absent,,-7334718598697473719,RHEL,RHEL 7.4,7.4,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            ",,,2,2,False,2,True,False,False,False,,,virtualized,,[-7334718598697473719],,absent,absent,absent,absent,,-7334718598697473719,RHEL,RHEL 7.5,7.5,,,[test_source],,,2017-07-18,,,,,,,,,,vmware,,,,,,,\r\n"  # noqa: E501
            "\r\n"
        )  # noqa
        # pylint: disable=line-too-long, consider-using-f-string
        details_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n1,details,%s,%s,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\nconnection_host,connection_port,connection_uuid,cpu_core_count,cpu_core_per_socket,cpu_count,cpu_hyperthreading,cpu_siblings,cpu_socket_count,date_anaconda_log,date_yum_history,etc_release_name,etc_release_release,etc_release_version,ifconfig_ip_addresses,uname_hostname,virt_num_guests,virt_num_running_guests,virt_type,virt_virt,virt_what_type\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[-7334718598697473719],-7334718598697473719,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[-7334718598697473719],-7334718598697473719,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.5,7.5,[-7334718598697473719],-7334718598697473719,1,1,vmware,virt-guest,vt\r\n\r\n\r\n"  # noqa: E501
            % (
                self.report_version,
                reports_dict.get("details_json").get("report_platform_id"),
                self.server_id,
            )
        )  # noqa
        renderer = ReportsGzipRenderer()
        mock_req = MockRequest(mask_rep=True)
        mock_renderer_context = {"request": mock_req}
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)  # pylint: disable=consider-using-with
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith("csv"):
                if "details" in file_contents:
                    assert file_contents == details_csv
                elif "deployments" in file_contents:
                    assert file_contents == deployments_csv
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

    def test_sha256sum(self):
        """Ensure SHA256SUM hashes are correct."""
        reports_dict = self.create_reports_dict()
        renderer = ReportsGzipRenderer()
        mock_req = MockRequest(mask_rep=True)
        mock_renderer_context = {"request": mock_req}
        tar_gz_result = renderer.render(
            reports_dict, renderer_context=mock_renderer_context
        )
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)  # pylint: disable=consider-using-with
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
        assert set(file2hash) == expected_hashed_filenames
        # recalculate hashes
        new_file2hash = {}
        for hashed_filename, calculated_hash in file2hash.items():
            file = filename_to_file[hashed_filename]
            file_contents = tar.extractfile(file).read()
            new_hash = hashlib.sha256(file_contents).hexdigest()
            new_file2hash[hashed_filename] = new_hash
        assert new_file2hash == file2hash, "SHA256SUM content is incorrect"
