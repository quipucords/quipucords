"""Integration test for network scan."""

from logging import getLogger
from unittest.mock import Mock

import pytest
from django.conf import settings

from api.models import SystemFingerprint
from constants import DataSources
from scanner.network.inspect_callback import HOST_DONE, InspectCallback
from scanner.network.utils import raw_facts_template
from tests.integration.test_smoker import Smoker
from tests.utils import raw_facts_generator
from tests.utils.facts import RawFactComparator, fact_expander
from utils import deepget

logger = getLogger(__name__)


@pytest.fixture
def expected_network_scan_facts():
    """Set of expected facts on network scan."""
    expected_fact_names = {
        "cloud_provider",
        "connection_host",
        "connection_port",
        "connection_timestamp",
        "connection_uuid",
        "cpu_core_count",
        "cpu_core_per_socket",
        "cpu_count",
        "cpu_hyperthreading",
        "cpu_model_name",
        "cpu_model_ver",
        "cpu_siblings",
        "cpu_socket_count",
        "cpu_vendor_id",
        "date_anaconda_log",
        "date_filesystem_create",
        "date_machine_id",
        "dmi_bios_vendor",
        "dmi_bios_version",
        "dmi_chassis_asset_tag",
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
        "etc_machine_id",
        "etc_release_name",
        "etc_release_release",
        "etc_release_version",
        "fuse_activemq_version",
        "fuse_camel_version",
        "fuse_cxf_version",
        "host_done",
        "hostnamectl",
        "ifconfig_ip_addresses",
        "ifconfig_mac_addresses",
        "insights_client_id",
        "installed_products",
        "ip_address_show_ipv4",
        "ip_address_show_mac",
        "jboss_activemq_ver",
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
        "subscription_manager_id",
        "system_memory_bytes",
        "system_purpose_json",
        "system_user_count",
        "uname_all",
        "uname_hostname",
        "uname_processor",
        "user_has_sudo",
        "virt_num_guests",
        "virt_num_running_guests",
        "virt_type",
        "virt_what",
        "yum_enabled_repolist",
    }
    if not settings.QUIPUCORDS_EXCLUDE_INTERNAL_FACTS:
        expected_fact_names |= {
            "internal_cpu_model_name_kvm",
            "internal_cpu_socket_count_cpuinfo",
            "internal_cpu_socket_count_dmi",
            "internal_distro_standard_release",
            "internal_dmi_chassis_asset_tag",
            "internal_dmi_system_product_name",
            "internal_dmi_system_uuid",
            "internal_have_chkconfig",
            "internal_have_dmidecode",
            "internal_have_ifconfig",
            "internal_have_ifconfig_user",
            "internal_have_ip",
            "internal_have_ip_user",
            "internal_have_java",
            "internal_have_locate",
            "internal_have_rct_user",
            "internal_have_rpm_user",
            "internal_have_subscription_manager",
            "internal_have_systemctl",
            "internal_have_tune2fs_user",
            "internal_have_unzip",
            "internal_have_virsh_user",
            "internal_have_virt_what",
            "internal_have_yum",
            "internal_host_started_processing_role",
            "internal_kvm_found",
            "internal_release_file",
            "internal_sys_manufacturer",
            "internal_system_user_count",
            "internal_xen_guest",
            "internal_xen_privcmd_found",
        }
    return expected_fact_names


@pytest.fixture
def fingerprint_fact_map(raw_facts):
    """Map fingerprint to raw fact name."""
    fact_map = {
        "architecture": "uname_processor",
        "bios_uuid": "dmi_system_uuid",
        "cloud_provider": "cloud_provider",
        "cpu_core_count": "cpu_core_count",
        "cpu_core_per_socket": "cpu_core_per_socket",
        "cpu_count": "cpu_count",
        "cpu_hyperthreading": "cpu_hyperthreading",
        "cpu_socket_count": "cpu_socket_count",
        "etc_machine_id": "etc_machine_id",
        "infrastructure_type": "virt_what/hostnamectl",
        "insights_client_id": "insights_client_id",
        "installed_products": "installed_products",
        "ip_addresses": "ip_address_show_ipv4/ifconfig_ip_addresses",
        "is_redhat": "redhat_packages_gpg_is_redhat",
        "mac_addresses": "ip_address_show_mac/ifconfig_mac_addresses",
        "name": "uname_hostname",
        "os_name": "etc_release_name",
        "os_release": "etc_release_release",
        "os_version": "etc_release_version",
        "redhat_certs": "redhat_packages_certs",
        "redhat_package_count": "redhat_packages_gpg_num_rh_packages",
        "subscription_manager_id": "subscription_manager_id",
        "system_addons": "system_purpose_json__addons",
        "system_creation_date": "date_filesystem_create/date_anaconda_log/registration_time/date_machine_id",  # noqa:E501
        "system_last_checkin_date": "connection_timestamp",
        "system_memory_bytes": "system_memory_bytes",
        "system_purpose": "system_purpose_json",
        "system_role": "system_purpose_json__role",
        "system_service_level_agreement": "system_purpose_json__service_level_agreement",  # noqa:E501
        "system_usage_type": "system_purpose_json__usage",
        "system_user_count": "system_user_count",
        "virtualized_type": "virt_type",
    }
    # system_creation_date is a special case and might not always be part of the report
    system_creation_date_comparator = RawFactComparator(
        fact_map["system_creation_date"]
    )
    valid_raw_facts = set(
        name for name, value in raw_facts.items() if value is not None
    )
    if valid_raw_facts not in system_creation_date_comparator:
        fact_map.pop("system_creation_date")
    return fact_map


@pytest.fixture
def unexpected_fingerprints():
    """Set of facts that wouldn't appear on network scans."""
    return {
        # sattelite / vcenter exclusive
        "virtual_host_name",
        "virtual_host_uuid",
        # vcenter exclusive
        "vm_cluster",
        "vm_datacenter",
        "vm_dns_name",
        "vm_host_core_count",
        "vm_host_socket_count",
        "vm_state",
        "vm_uuid",
        # openshift
        "container_images",
        "container_labels",
    }


def test_sanity_check_raw_fact_matches(
    expected_network_scan_facts, fingerprint_fact_map, unexpected_fingerprints
):
    """Ensure raw facts mapped to fingerprint facts match known facts."""
    raw_facts_for_fingerprints = set()
    for fact in fingerprint_fact_map.values():
        raw_facts_for_fingerprints |= fact_expander(fact)
    assert "registration_time" in raw_facts_for_fingerprints
    # remove "registration_time" as this is a satellite fact
    raw_facts_for_fingerprints -= {"registration_time"}

    assert raw_facts_for_fingerprints < expected_network_scan_facts, (
        f"Expected facts not found: "
        f"{raw_facts_for_fingerprints - expected_network_scan_facts}"
    )
    # excluding vcenter/satellite exclusives, all fingerprints should be the ones
    # expected on fingerprint_fact_map
    network_scan_fingerprints = (
        SystemFingerprint.get_valid_fact_names() - unexpected_fingerprints
    )
    assert network_scan_fingerprints == set(fingerprint_fact_map.keys())


@pytest.fixture
def target_ip(faker):
    """Fake target machine IP used during testing."""
    return faker.ipv4()


@pytest.fixture
def raw_facts(target_ip):
    """Return expected raw facts."""
    _raw_facts = next(raw_facts_generator(DataSources.NETWORK.value, n=1))
    # HOST_DONE must be true so the scan can be considered successful; connection_host
    # must match scanned system ip (target_ip)
    _raw_facts.update(**{HOST_DONE: True, "connection_host": target_ip})
    return _raw_facts


class PatchedAnsibleRunner:
    """Class based helper that patches ansible_runner.run."""

    def __init__(self, event_data: list[dict]):
        self._runner_counter = 0
        self._event_data = event_data

    def __call__(self, **kwargs):
        """Patched ansible_runner.run.

        Should be used as a side effect of 'Mock.patch'.
        """
        # ansible_runner will be invoked twice during our test: once during connect
        # phase, and once during inspect phase. During connect phase we need to patch it
        # differently, hence the need of _runner_counter variable
        if self._runner_counter < len(self._event_data):
            self._patched_ansible_runner_for_connect_scan(**kwargs)
        fake_ansible_result = Mock()
        fake_ansible_result.stdout.read.side_effect = lambda: "ansible stdout"
        fake_ansible_result.stderr.read.side_effect = lambda: "ansible stderr"
        fake_ansible_result.status = "successful"
        self._runner_counter += 1
        return fake_ansible_result

    def _patched_ansible_runner_for_connect_scan(self, *, event_handler, **kwargs):
        event = self._event_data[self._runner_counter]
        event_handler(event)


@pytest.fixture
def patched_scan_data(mocker, target_ip, raw_facts):
    """Patched data for network scan.

    This fixture aims to mock very surgical points on network scan, allowing to exercise
    most of the code.
    """

    def _patched_process(scan_task, previous_host_facts, fact_key, fact_value, host):
        # should be used as a replacement of scanner.network.processing.process
        return fact_value

    # bare bones ansible event for a successful "connection phase"
    event_data = {
        "event": "runner_on_ok",
        "event_data": {"res": {"rc": 0}, "host": target_ip},
    }

    mocker.patch("ansible_runner.run", side_effect=PatchedAnsibleRunner([event_data]))
    # patching ansible_runner.run should cover connect phase, but this mocking mechanism
    # is not providing anything for inspect phase. we will cover that by mocking its
    # callback class
    raw_facts_per_ip = {target_ip: raw_facts}
    mocker.patch.object(InspectCallback, "ansible_facts", raw_facts_per_ip)
    # Finally, given we are generating "raw facts" already post processed, we need to
    # turn off the real post processor.
    mocker.patch("scanner.network.inspect.process", side_effect=_patched_process)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("patched_scan_data")
class TestNetworkScan(Smoker):
    """Smoke test network scanner."""

    SOURCE_NAME = "testing source"
    SOURCE_TYPE = DataSources.NETWORK.value

    @pytest.fixture
    def credential_payload(self):
        """Return payload to create credential."""
        return {
            "name": "testing credential",
            "username": "<USER>",
            "password": "<PASSWORD>",
        }

    @pytest.fixture
    def source_payload(self, target_ip):
        """Return Payload used to create source."""
        return {
            "hosts": [target_ip],
            "name": self.SOURCE_NAME,
        }

    @pytest.fixture
    def expected_facts(self, raw_facts):
        """Return expected facts."""
        facts = raw_facts_template()
        facts.update(raw_facts)
        return [facts]

    @pytest.fixture
    def expected_fingerprints(self, fingerprint_fact_map, mocker, raw_facts):
        """Return expected fingerprint dict."""
        fingerprints = {key: mocker.ANY for key in fingerprint_fact_map.keys()}
        # ONLY raw facts with direct map to a fingerprint
        raw_fact2fingerprint = (
            ("uname_hostname", "name"),
            ("uname_processor", "architecture"),
            ("redhat_packages_gpg_num_rh_packages", "redhat_package_count"),
            ("redhat_packages_certs", "redhat_certs"),
            ("redhat_packages_gpg_is_redhat", "is_redhat"),
            ("etc_machine_id", "etc_machine_id"),
            ("etc_release_name", "os_name"),
            ("etc_release_version", "os_version"),
            ("etc_release_release", "os_release"),
            ("installed_products", "installed_products"),
            ("cpu_count", "cpu_count"),
            ("dmi_system_uuid", "bios_uuid"),
            ("subscription_manager_id", "subscription_manager_id"),
            ("cpu_socket_count", "cpu_socket_count"),
            ("cpu_core_count", "cpu_core_count"),
            ("cpu_core_per_socket", "cpu_core_per_socket"),
            ("cpu_hyperthreading", "cpu_hyperthreading"),
            ("insights_client_id", "insights_client_id"),
            ("cloud_provider", "cloud_provider"),
            ("system_purpose_json", "system_purpose"),
            ("system_purpose_json__role", "system_role"),
            ("system_purpose_json__addons", "system_addons"),
            (
                "system_purpose_json__service_level_agreement",
                "system_service_level_agreement",
            ),
            ("system_purpose_json__usage", "system_usage_type"),
            ("virt_type", "virtualized_type"),
            ("system_memory_bytes", "system_memory_bytes"),
        )
        for raw_name, fp_name in raw_fact2fingerprint:
            fingerprints[fp_name] = deepget(raw_facts, raw_name)
        # installed_products formatter will transform None -> []
        if fingerprints["installed_products"] is None:
            fingerprints["installed_products"] = []
        return fingerprints

    @pytest.fixture
    def expected_products(self, mocker):
        """Return expected products."""
        # TODO: this should be expanded to match expected products (which vary based on
        # raw_facts)
        return mocker.ANY
