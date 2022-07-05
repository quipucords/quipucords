# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Integration test for network scan."""

import json
import tarfile
from datetime import datetime
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
from tests import constants
from tests.utils.facts import RawFactComparator

logger = getLogger(__name__)


def load_json_from_tarball(filename_json, tarball):
    """Extract a json as dict from given TarFile interface."""
    return json.loads(tarball.extractfile(filename_json).read())


@pytest.fixture
def expected_network_scan_facts():
    """Set of expected facts on network scan."""
    return {
        "business_central_candidates",
        "business_central_candidates_eap",
        "cloud_provider",
        "connection_host",
        "connection_port",
        "connection_timestamp",
        "connection_uuid",
        "cpu_bogomips",
        "cpu_core_count",
        "cpu_core_per_socket",
        "cpu_count",
        "cpu_cpu_family",
        "cpu_hyperthreading",
        "cpu_model_name",
        "cpu_model_ver",
        "cpu_siblings",
        "cpu_socket_count",
        "cpu_vendor_id",
        "date_anaconda_log",
        "date_date",
        "date_filesystem_create",
        "date_machine_id",
        "date_yum_history",
        "decision_central_candidates",
        "decision_central_candidates_eap",
        "dmi_bios_vendor",
        "dmi_bios_version",
        "dmi_chassis_asset_tag",
        "dmi_processor_family",
        "dmi_system_manufacturer",
        "dmi_system_product_name",
        "dmi_system_uuid",
        "eap5_home_candidates",
        "eap5_home_ls_jboss_as",
        "eap5_home_readme_html",
        "eap5_home_run_jar_manifest",
        "eap5_home_run_jar_version",
        "eap5_home_version_txt",
        "eap_home_bin",
        "eap_home_candidates",
        "eap_home_jboss_modules_manifest",
        "eap_home_jboss_modules_version",
        "eap_home_layers",
        "eap_home_layers_conf",
        "eap_home_ls",
        "eap_home_readme_txt",
        "eap_home_version_txt",
        "etc_issue",
        "etc_machine_id",
        "etc_release_name",
        "etc_release_release",
        "etc_release_version",
        "fuse_activemq_version",
        "fuse_camel_version",
        "fuse_cxf_version",
        "host_done",
        "ifconfig_ip_addresses",
        "ifconfig_mac_addresses",
        "insights_client_id",
        "instnum",
        "jboss_activemq_ver",
        "jboss_brms_business_central_candidates",
        "jboss_brms_decision_central_candidates",
        "jboss_brms_drools_core_ver",
        "jboss_brms_kie_api_ver",
        "jboss_brms_kie_in_business_central",
        "jboss_brms_kie_server_candidates",
        "jboss_brms_kie_war_ver",
        "jboss_brms_locate_kie_api",
        "jboss_brms_manifest_mf",
        "jboss_camel_ver",
        "jboss_cxf_ver",
        "jboss_eap_chkconfig",
        "jboss_eap_common_files",
        "jboss_eap_find_jboss_modules_jar",
        "jboss_eap_id_jboss",
        "jboss_eap_jar_ver",
        "jboss_eap_locate_jboss_modules_jar",
        "jboss_eap_packages",
        "jboss_eap_run_jar_ver",
        "jboss_eap_running_paths",
        "jboss_eap_systemctl_unit_files",
        "jboss_fuse_activemq_ver",
        "jboss_fuse_camel_ver",
        "jboss_fuse_chkconfig",
        "jboss_fuse_cxf_ver",
        "jboss_fuse_on_eap_activemq_ver",
        "jboss_fuse_on_eap_camel_ver",
        "jboss_fuse_on_eap_cxf_ver",
        "jboss_fuse_on_karaf_activemq_ver",
        "jboss_fuse_on_karaf_camel_ver",
        "jboss_fuse_on_karaf_cxf_ver",
        "jboss_fuse_systemctl_unit_files",
        "jboss_processes",
        "jws_has_cert",
        "jws_has_eula_txt_file",
        "jws_home",
        "jws_home_candidates",
        "jws_installed_with_rpm",
        "jws_version",
        "karaf_find_karaf_jar",
        "karaf_home_bin_fuse",
        "karaf_home_system_org_jboss",
        "karaf_homes",
        "karaf_locate_karaf_jar",
        "karaf_running_processes",
        "kie_search_candidates",
        "kie_server_candidates",
        "kie_server_candidates_eap",
        "last_booted_at",
        "redhat_packages_certs",
        "redhat_packages_gpg_is_redhat",
        "redhat_packages_gpg_last_built",
        "redhat_packages_gpg_last_installed",
        "redhat_packages_gpg_num_installed_packages",
        "redhat_packages_gpg_num_rh_packages",
        "redhat_release_name",
        "redhat_release_release",
        "redhat_release_version",
        "subman",
        "subman_consumed",
        "subman_cpu_core_per_socket",
        "subman_cpu_cpu",
        "subman_cpu_cpu_socket",
        "subman_overall_status",
        "subman_virt_host_type",
        "subman_virt_is_guest",
        "subman_virt_uuid",
        "system_purpose_json",
        "system_user_count",
        "systemid",
        "tomcat_is_part_of_redhat_product",
        "uname_all",
        "uname_hardware_platform",
        "uname_hostname",
        "uname_kernel",
        "uname_os",
        "uname_processor",
        "user_has_sudo",
        "user_login_history",
        "virt_num_guests",
        "virt_num_running_guests",
        "virt_type",
        "virt_virt",
        "virt_what_type",
        "yum_enabled_repolist",
    }


@pytest.fixture
def expected_middleware_names():
    """Middleware names."""
    return {"JBoss BRMS", "JBoss EAP", "JBoss Web Server", "JBoss Fuse"}


@pytest.fixture
def fingerprint_fact_map():
    """Map fingerprint to raw fact name."""
    return {
        "architecture": "uname_processor",
        "bios_uuid": "dmi_system_uuid",
        "cloud_provider": "cloud_provider",
        "cpu_core_count": "cpu_core_count",
        "cpu_core_per_socket": "cpu_core_per_socket",
        "cpu_count": "cpu_count",
        "cpu_hyperthreading": "cpu_hyperthreading",
        "cpu_socket_count": "cpu_socket_count",
        "etc_machine_id": "etc_machine_id",
        "infrastructure_type": "virt_type",
        "is_redhat": "redhat_packages_gpg_is_redhat",
        "name": "uname_hostname",
        "os_name": "etc_release_name",
        "os_release": "etc_release_release",
        "os_version": "etc_release_version",
        "redhat_certs": "redhat_packages_certs",
        "redhat_package_count": "redhat_packages_gpg_num_rh_packages",
        "subscription_manager_id": "subman_virt_uuid",
        "system_creation_date": "date_machine_id",
        "system_last_checkin_date": "connection_timestamp",
        "system_user_count": "system_user_count",
        "user_login_history": "user_login_history",
        "virtualized_type": "virt_type",
    }


@pytest.mark.slow
@pytest.mark.integration
class TestNetworkScan:
    """Smoke test network scan."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "network"

    @pytest.fixture(scope="class")
    def credential_id(self, apiclient):
        """Create network credentials through api and return credentials identifier."""
        response = apiclient.post(
            "credentials/",
            json={
                "username": constants.SCAN_TARGET_USERNAME,
                "password": constants.SCAN_TARGET_PASSWORD,
                "name": "testing credential",
                "cred_type": self.SOURCE_TYPE,
                "become_method": "sudo",
                "become_password": constants.SCAN_TARGET_PASSWORD,
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture(scope="class")
    def source_id(self, apiclient, credential_id, scan_target_container):
        """Register source for network scan through api and return its identifier."""
        response = apiclient.post(
            "sources/",
            json={
                "source_type": self.SOURCE_TYPE,
                "credentials": [credential_id],
                "hosts": [scan_target_container.ips.primary],
                "name": self.SOURCE_NAME,
                "port": constants.SCAN_TARGET_SSH_PORT,
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture(scope="class")
    def scan_id(self, apiclient, source_id):
        """Create a scan and return its identifier."""
        create_scan_response = apiclient.post(
            "scans/",
            json={"name": "test scan", "sources": [source_id]},
        )
        assert create_scan_response.ok, create_scan_response.text
        scan_id = create_scan_response.json()["id"]
        return scan_id

    @pytest.fixture(scope="class")
    def scan_response(self, apiclient, scan_id):
        """Start a scan job and poll its results endpoint until completion."""
        create_scan_job_response = apiclient.post(f"scans/{scan_id}/jobs/")
        assert create_scan_job_response.ok, create_scan_job_response.text

        response = apiclient.get(f"scans/{scan_id}/")
        attempts = 1
        assert response.ok, response.text

        completed_status = {ScanTask.COMPLETED, ScanTask.CANCELED, ScanTask.FAILED}
        while (
            scan_status := response.json()["most_recent"]["status"]
        ) not in completed_status and attempts < self.MAX_RETRIES:
            attempts += 1
            backoff = 2**attempts
            sleep(backoff)
            response = apiclient.get(f"scans/{scan_id}/")
            assert response.ok, response.text

        assert scan_status == ScanTask.COMPLETED, response.text

        return response

    @pytest.fixture(scope="class")
    def report_id(self, scan_response):
        """Return the latest report id from performed scan."""
        return scan_response.json()["most_recent"]["report_id"]

    def test_details_report(self, apiclient, expected_network_scan_facts, report_id):
        """Sanity check details report."""
        response = apiclient.get(f"reports/{report_id}/details/")
        assert response.ok, response.text
        report_details_dict = response.json()
        expected_details_report = {
            "report_id": report_id,
            "report_platform_id": mock.ANY,
            "report_type": "details",
            "report_version": mock.ANY,
            SOURCES_KEY: [
                {
                    "facts": [
                        {fact: mock.ANY for fact in expected_network_scan_facts},
                    ],
                    "report_version": mock.ANY,
                    "server_id": mock.ANY,
                    "source_name": self.SOURCE_NAME,
                    "source_type": self.SOURCE_TYPE,
                }
            ],
        }
        assert report_details_dict == expected_details_report

        some_expected_facts = dict(
            etc_release_name="Red Hat Enterprise Linux",
            redhat_packages_gpg_is_redhat=True,
            date_machine_id=datetime.utcnow().date().isoformat(),
            user_has_sudo=True,
        )
        report_details_facts = report_details_dict["sources"][0]["facts"][0]
        assert report_details_facts | some_expected_facts == report_details_facts

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
                has_sudo=True,
            )
        return metadata

    def test_deployments_report(  # pylint: disable=too-many-arguments
        self,
        apiclient,
        expected_fingerprint_metadata,
        expected_middleware_names,
        fingerprint_fact_map,
        report_id,
    ):
        """Sanity check report deployments json structure."""
        response = apiclient.get(f"reports/{report_id}/deployments/")
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
            META_DATA_KEY: expected_fingerprint_metadata,
            PRODUCTS_KEY: mock.ANY,
            **{fingerprint: mock.ANY for fingerprint in fingerprint_fact_map.keys()},
        }

        assert {
            product["name"] for product in fingerprints_dict["products"]
        } == expected_middleware_names

    def test_compare_standalone_json_reports_with_tarball(self, apiclient, report_id):
        """Compare individual reports with the ones bundled on the tarball endpoint."""
        details_response = apiclient.get(f"reports/{report_id}/details/")
        assert details_response.ok, details_response.json()

        deployments_response = apiclient.get(f"reports/{report_id}/deployments/")
        assert deployments_response.ok, deployments_response.json()

        full_report_response = apiclient.get(f"reports/{report_id}/")
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
