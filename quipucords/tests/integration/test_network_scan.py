"""Integration test for network scan."""

from logging import getLogger

import pytest
from django.conf import settings

from api.models import SystemFingerprint
from tests.utils.facts import fact_expander

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
        "virt_virt",
        "virt_what_type",
        "yum_enabled_repolist",
    }
    if not settings.QPC_EXCLUDE_INTERNAL_FACTS:
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
            "internal_have_rct",
            "internal_have_rpm",
            "internal_have_subscription_manager",
            "internal_have_systemctl",
            "internal_have_tune2fs_user",
            "internal_have_unzip",
            "internal_have_virsh",
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
        "infrastructure_type": "virt_what_type/virt_type",
        "insights_client_id": "insights_client_id",
        "installed_products": "installed_products",
        "ip_addresses": "ip_address_show_ipv4",
        "is_redhat": "redhat_packages_gpg_is_redhat",
        "mac_addresses": "ip_address_show_mac",
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
