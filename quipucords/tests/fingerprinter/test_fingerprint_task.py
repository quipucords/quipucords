"""Test the fact engine API."""

from copy import deepcopy
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import pytest
from django.db import DataError

from api.deployments_report.model import SystemFingerprint
from api.models import DeploymentsReport, Report, ServerInformation, Source
from api.scantask.model import ScanTask
from constants import DataSources
from fingerprinter.constants import ENTITLEMENTS_KEY, META_DATA_KEY, PRODUCTS_KEY
from fingerprinter.runner import (
    FINGERPRINT_GLOBAL_ID_KEY,
    NETWORK_SATELLITE_MERGE_KEYS,
    NETWORK_VCENTER_MERGE_KEYS,
    FingerprintTaskRunner,
)
from scanner.network.utils import raw_facts_template as network_template
from scanner.satellite.utils import raw_facts_template as satellite_template
from scanner.vcenter.utils import raw_facts_template as vcenter_template
from tests.scanner.test_util import create_scan_job

SUBMAN_CONSUMED = [{"name": "Red Hat JBoss Fuse", "entitlement_id": "ESA0009"}]
SAT_ENTITLEMENTS = [{"name": "Satellite Tools 6.3"}]

EXPECTED_FINGERPRINT_MAP_NETWORK = {
    "architecture": "uname_processor",
    "bios_uuid": "dmi_system_uuid",
    "cloud_provider": "cloud_provider",
    "cpu_core_count": "cpu_core_count",
    "cpu_core_per_socket": "cpu_core_per_socket",
    "cpu_count": "cpu_count",
    "cpu_hyperthreading": "cpu_hyperthreading",
    "cpu_socket_count": "cpu_socket_count",
    "date_anaconda_log": "date_anaconda_log",
    "date_filesystem_create": "date_filesystem_create",
    "date_machine_id": "date_machine_id",
    "date_yum_history": "date_yum_history",
    "etc_machine_id": "etc_machine_id",
    "infrastructure_type": "virt_what_type/virt_type",
    "insights_client_id": "insights_client_id",
    "installed_products": "installed_products",
    "ip_addresses": "ifconfig_ip_addresses",
    "is_redhat": "redhat_packages_gpg_is_redhat",
    "mac_addresses": "ifconfig_mac_addresses",
    "name": "uname_hostname",
    "os_name": "etc_release_name",
    "os_release": "etc_release_release",
    "os_version": "etc_release_version",
    "redhat_certs": "redhat_packages_certs",
    "redhat_package_count": "redhat_packages_gpg_num_rh_packages",
    "subscription_manager_id": "subscription_manager_id",
    "system_addons": "system_purpose_json__addons",
    "system_last_checkin_date": "connection_timestamp",
    "system_memory_bytes": "system_memory_bytes",
    "system_purpose": "system_purpose_json",
    "system_role": "system_purpose_json__role",
    "system_service_level_agreement": "system_purpose_json__service_level_agreement",
    "system_usage_type": "system_purpose_json__usage",
    "system_user_count": "system_user_count",
    "user_login_history": "user_login_history",
    "virtualized_type": "virt_type",
}
EXPECTED_FINGERPRINT_MAP_SATELLITE = {
    "architecture": "architecture",
    "cpu_core_count": "cores",
    "cpu_count": "cores",
    "cpu_socket_count": "num_sockets",
    "infrastructure_type": "is_virtualized",
    "ip_addresses": "ip_addresses",
    "is_redhat": "os_release",
    "mac_addresses": "mac_addresses",
    "name": "hostname",
    "os_name": "os_name",
    "os_release": "os_release",
    "os_version": "os_version",
    "registration_time": "registration_time",
    "subscription_manager_id": "uuid",
    "system_last_checkin_date": "last_checkin_time",
    "virtual_host_name": "virtual_host_name",
    "virtual_host_uuid": "virtual_host_uuid",
    "virtualized_type": "virt_type",
}
EXPECTED_FINGERPRINT_MAP_VCENTER = {
    "architecture": "uname_processor",
    "cpu_count": "vm.cpu_count",
    "infrastructure_type": "vcenter_source",
    "ip_addresses": "vm.ip_addresses",
    "is_redhat": "vm.os",
    "mac_addresses": "vm.mac_addresses",
    "name": "vm.name",
    "os_release": "vm.os",
    "system_last_checkin_date": "vm.last_check_in",
    "system_memory_bytes": "vm.memory_size",
    "virtual_host_name": "vm.host.name",
    "virtual_host_uuid": "vm.host.uuid",
    "vm_cluster": "vm.cluster",
    "vm_datacenter": "vm.datacenter",
    "vm_dns_name": "vm.dns_name",
    "vm_host_core_count": "vm.host.cpu_cores",
    "vm_host_socket_count": "vm.host.cpu_count",
    "vm_state": "vm.state",
    "vm_uuid": "vm.uuid",
}

PRODUCTS = [
    {"name": "JBoss EAP", "presence": "absent"},
    {"name": "JBoss Fuse", "presence": "absent"},
    {"name": "JBoss BRMS", "presence": "absent"},
    {"name": "JBoss Web Server", "presence": "absent", "version": []},
]


@pytest.fixture
def server_id():
    """Get the server ID for tests."""
    return ServerInformation.create_or_retrieve_server_id()


@pytest.fixture
def source():
    """Create a Source for tests."""
    return Source.objects.create(
        name="source1",
        hosts=["1.2.3.4"],
        source_type="network",
        port=22,
    )


@pytest.fixture
def scan_job(source):
    """Create a ScanJob for tests."""
    scan_job, _ = create_scan_job(source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
    return scan_job


@pytest.fixture
def fingerprint_task(scan_job):
    """Get the fingerprint task."""
    return scan_job.tasks.filter(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT).last()


@pytest.fixture
def fingerprint_task_runner(scan_job, fingerprint_task):
    """Create a FingerprintTaskRunner for tests."""
    return FingerprintTaskRunner(scan_job, fingerprint_task)


################################################################
# Helper functions
################################################################
def _create_network_details_report_json(  # noqa: PLR0913, PLR0912, PLR0915, C901
    report_id=1,
    source_name="source1",
    source_type=DataSources.NETWORK,
    cpu_count=1,
    etc_release_name="RHEL",
    etc_release_version="7.4 (Maipo)",
    etc_release_release="RHEL 7.4 (Maipo)",
    ifconfig_ip_addresses=None,
    ifconfig_mac_addresses=None,
    dmi_system_uuid=1234,
    subman_virt_uuid=4567,
    subman_consumed=SUBMAN_CONSUMED,
    subscription_manager_id=42,
    connection_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
    connection_host="1.2.3.4",
    connection_port=22,
    cpu_socket_count=2,
    cpu_core_count=2,
    date_yum_history="2017-07-18",
    date_filesystem_create="2017-06-17",
    date_anaconda_log="2017-05-17",
    date_machine_id="2017-04-17",
    system_purpose_json=None,
    virt_virt="virt-guest",
    virt_type="vmware",
    virt_num_guests=1,
    virt_num_running_guests=1,
    virt_what_type="vt",
    is_redhat=True,
    redhat_certs="fake certs",
    redhat_package_count=100,
    architecture="x86_64",
    user_has_sudo=True,
):
    """Create an in memory details report for tests."""
    fact = network_template()
    if source_name:
        fact["source_name"] = source_name
    if source_type:
        fact["source_type"] = source_type
    if cpu_count:
        fact["cpu_count"] = cpu_count
    if etc_release_name:
        fact["etc_release_name"] = etc_release_name
    if etc_release_version:
        fact["etc_release_version"] = etc_release_version
    if etc_release_release:
        fact["etc_release_release"] = etc_release_release

    if ifconfig_ip_addresses:
        fact["ifconfig_ip_addresses"] = ifconfig_ip_addresses
    else:
        fact["ifconfig_ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

    if ifconfig_mac_addresses:
        fact["ifconfig_mac_addresses"] = list(
            map(lambda x: x.lower(), ifconfig_mac_addresses)
        )
    else:
        fact["ifconfig_mac_addresses"] = ["mac1", "mac2"]

    if dmi_system_uuid:
        fact["dmi_system_uuid"] = dmi_system_uuid
    if subman_virt_uuid:
        fact["subman_virt_uuid"] = subman_virt_uuid
    if subman_consumed:
        fact["subman_consumed"] = subman_consumed
    fact["subscription_manager_id"] = subscription_manager_id
    if connection_uuid:
        fact["connection_uuid"] = connection_uuid
    if connection_host:
        fact["connection_host"] = connection_host
        fact["uname_hostname"] = connection_host
    if connection_port:
        fact["connection_port"] = connection_port
    if cpu_socket_count:
        fact["cpu_socket_count"] = cpu_socket_count
    if cpu_core_count:
        fact["cpu_core_count"] = cpu_core_count
    if date_anaconda_log:
        fact["date_anaconda_log"] = date_anaconda_log
    if date_yum_history:
        fact["date_yum_history"] = date_yum_history
    if date_filesystem_create:
        fact["date_filesystem_create"] = date_filesystem_create
    if date_machine_id:
        fact["date_machine_id"] = date_machine_id
    if system_purpose_json:
        fact["system_purpose_json"] = system_purpose_json
    if virt_virt:
        fact["virt_virt"] = virt_virt
    if virt_type:
        fact["virt_type"] = virt_type
    if virt_num_guests:
        fact["virt_num_guests"] = virt_num_guests
    if virt_num_running_guests:
        fact["virt_num_running_guests"] = virt_num_running_guests
    if virt_what_type:
        fact["virt_what_type"] = virt_what_type
    if is_redhat:
        fact["redhat_packages_gpg_is_redhat"] = is_redhat
    if redhat_certs:
        fact["redhat_packages_certs"] = redhat_certs
    if redhat_package_count:
        fact["redhat_packages_gpg_num_rh_packages"] = redhat_package_count
    if architecture:
        fact["uname_processor"] = architecture

    fact["user_has_sudo"] = user_has_sudo

    details_report = {"id": report_id, "facts": [fact]}
    return details_report


def _create_vcenter_details_report_json(  # noqa: PLR0913, PLR0912, C901
    report_id=1,
    source_name="source2",
    source_type=DataSources.VCENTER,
    vm_cpu_count=2,
    vm_os="RHEL 7.3",
    vm_mac_addresses=None,
    vm_ip_addresses=None,
    vm_name="TestMachine",
    vm_state="On",
    vm_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
    vm_dns_name="site.com",
    vm_host_name="1.2.3.4",
    vm_host_cpu_count=8,
    vm_host_core_count=8,
    vm_datacenter="NY",
    vm_cluster="23sd",
    architecture="x86_64",
    is_redhat=True,
):
    """Create an in memory details report for tests."""
    fact = vcenter_template()
    if source_name:
        fact["source_name"] = source_name
    if source_type:
        fact["source_type"] = source_type
    if vm_cpu_count:
        fact["vm.cpu_count"] = vm_cpu_count
    if vm_os:
        fact["vm.os"] = vm_os

    if vm_ip_addresses:
        fact["vm.ip_addresses"] = vm_ip_addresses
    else:
        fact["vm.ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

    if vm_mac_addresses:
        fact["vm.mac_addresses"] = list(map(lambda x: x.lower(), vm_mac_addresses))
    else:
        fact["vm.mac_addresses"] = ["mac1", "mac2"]

    if vm_name:
        fact["vm.name"] = vm_name
    if vm_state:
        fact["vm.state"] = vm_state
    if vm_uuid:
        fact["vm.uuid"] = vm_uuid
    if vm_dns_name:
        fact["vm.dns_name"] = vm_dns_name
    if vm_host_name:
        fact["vm.host.name"] = vm_host_name
    if vm_host_cpu_count:
        fact["vm.host.cpu_count"] = vm_host_cpu_count
    if vm_host_core_count:
        fact["vm.host.cpu_cores"] = vm_host_core_count
    if vm_datacenter:
        fact["vm.datacenter"] = vm_datacenter
    if vm_cluster:
        fact["vm.cluster"] = vm_cluster
    if architecture:
        fact["uname_processor"] = architecture
    if "red hat enterprise linux" in vm_os.lower() or "rhel" in vm_os.lower():
        fact["is_redhat"] = is_redhat
    details_report = {"id": report_id, "facts": [fact]}
    return details_report


def _create_satellite_details_report_json(  # noqa: PLR0913, PLR0912, C901
    report_id=1,
    source_name="source3",
    source_type=DataSources.SATELLITE,
    hostname="9.8.7.6",
    os_name="RHEL",
    os_release="RHEL 7.3",
    os_version=7.3,
    mac_addresses=None,
    ip_addresses=None,
    cores=32,
    registration_time="2017-03-18",
    uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
    virt_type="lxc",
    is_virtualized=True,
    virtual_host="9.3.4.6",
    num_sockets=8,
    entitlements=SAT_ENTITLEMENTS,
    architecture="x86_64",
    is_redhat=True,
):
    """Create an in memory details report for tests."""
    fact = satellite_template()
    if source_name:
        fact["source_name"] = source_name
    if source_type:
        fact["source_type"] = source_type
    if hostname:
        fact["hostname"] = hostname
    if os_name:
        fact["os_name"] = os_name
    if os_release:
        fact["os_release"] = os_release
    if os_version:
        fact["os_version"] = os_version

    if ip_addresses:
        fact["ip_addresses"] = ip_addresses
    else:
        fact["ip_addresses"] = ["1.2.3.4", "2.3.4.5"]

    if mac_addresses:
        fact["mac_addresses"] = list(map(lambda x: x.lower(), mac_addresses))
    else:
        fact["mac_addresses"] = ["mac1", "mac2"]

    if registration_time:
        fact["registration_time"] = registration_time

    if cores:
        fact["cores"] = cores
    if uuid:
        fact["uuid"] = uuid
    if virt_type:
        fact["virt_type"] = virt_type
    if is_virtualized:
        fact["is_virtualized"] = is_virtualized
    if virtual_host:
        fact["virtual_host"] = virtual_host
    if num_sockets:
        fact["num_sockets"] = num_sockets
    if entitlements:
        fact["entitlements"] = entitlements
    if architecture:
        fact["architecture"] = architecture
    if "red hat enterprise linux" in os_name.lower() or "rhel" in os_name.lower():
        fact["is_redhat"] = is_redhat

    details_report = {"id": report_id, "facts": [fact]}
    return details_report


def _validate_network_result(fingerprint, fact):
    """Help to validate fields."""
    assert fact.get("connection_host") == fingerprint.get("name")
    assert fact.get("etc_release_name") == fingerprint.get("os_name")
    assert fact.get("etc_release_release") == fingerprint.get("os_release")
    assert fact.get("etc_release_version") == fingerprint.get("os_version")
    assert fact.get("ifconfig_ip_addresses") == fingerprint.get("ip_addresses")
    assert fact.get("ifconfig_mac_addresses") == fingerprint.get("mac_addresses")
    assert fact.get("cpu_count") == fingerprint.get("cpu_count")
    assert fact.get("dmi_system_uuid") == fingerprint.get("bios_uuid")
    assert fact.get("subscription_manager_id") == fingerprint.get(
        "subscription_manager_id"
    )
    assert fact.get("cpu_socket_count") == fingerprint.get("cpu_socket_count")
    assert fact.get("cpu_core_count") == fingerprint.get("cpu_core_count")

    assert fact.get("date_anaconda_log") == fingerprint.get("date_anaconda_log")
    assert fact.get("date_yum_history") == fingerprint.get("date_yum_history")
    assert fact.get("date_machine_id") == fingerprint.get("date_machine_id")
    assert fact.get("date_filesystem_create") == fingerprint.get(
        "date_filesystem_create"
    )
    assert "virtualized" == fingerprint.get("infrastructure_type")

    assert fact.get("virt_type") == fingerprint.get("virtualized_type")
    assert fact.get("uname_processor") == fingerprint.get("architecture")
    assert fact.get("redhat_packages_certs") == fingerprint.get("redhat_certs")
    assert fact.get("redhat_packages_gpg_is_redhat") == fingerprint.get("is_redhat")
    assert fact.get("redhat_packages_gpg_num_rh_packages") == fingerprint.get(
        "redhat_package_count"
    )
    if system_purpose_json := fact.get("system_purpose_json"):
        assert system_purpose_json == fingerprint.get("system_purpose")
        assert system_purpose_json.get("role") == fingerprint.get("system_role")
        assert system_purpose_json.get("addons") == fingerprint.get("system_addons")
        assert system_purpose_json.get("service_level_agreement") == fingerprint.get(
            "system_service_level_agreement"
        )
        assert system_purpose_json.get("usage") == fingerprint.get("system_usage_type")
    else:
        assert fingerprint.get("system_role") is None
        assert fingerprint.get("system_addons") is None
        assert fingerprint.get("system_service_level_agreement") is None
        assert fingerprint.get("system_usage_type") is None


def _validate_vcenter_result(fingerprint, fact):
    """Help to validate fields."""
    if fact.get("vm.dns_name"):
        assert fact.get("vm.dns_name") == fingerprint.get("name")
    else:
        assert fact.get("vm.name") == fingerprint.get("name")
    assert fact.get("vm.os") == fingerprint.get("os_release")
    assert fact.get("vm.ip_addresses") == fingerprint.get("ip_addresses")
    assert fact.get("vm.mac_addresses") == fingerprint.get("mac_addresses")
    assert fact.get("vm.cpu_count") == fingerprint.get("cpu_count")
    assert fact.get("vm.state") == fingerprint.get("vm_state")
    assert fact.get("vm.uuid") == fingerprint.get("vm_uuid")
    assert fact.get("vm.dns_name") == fingerprint.get("vm_dns_name")
    assert fact.get("vm.host.name") == fingerprint.get("virtual_host_name")
    assert fact.get("vm.host.cpu_count") == fingerprint.get("vm_host_socket_count")
    assert fact.get("vm.host.cpu_cores") == fingerprint.get("vm_host_core_count")
    assert fact.get("vm.datacenter") == fingerprint.get("vm_datacenter")
    assert fact.get("vm.cluster") == fingerprint.get("vm_cluster")
    assert fact.get("uname_processor") == fingerprint.get("architecture")
    assert fact.get("is_redhat") == fingerprint.get("is_redhat")


def _validate_satellite_result(fingerprint, fact):
    """Help to validate fields."""
    assert fact.get("hostname") == fingerprint.get("name")
    assert fact.get("os_name") == fingerprint.get("os_name")
    assert fact.get("os_release") == fingerprint.get("os_release")
    assert fact.get("os_version") == fingerprint.get("os_version")
    assert fact.get("cores") == fingerprint.get("cpu_count")
    assert fact.get("ip_addresses") == fingerprint.get("ip_addresses")
    assert fact.get("mac_addresses") == fingerprint.get("mac_addresses")
    assert fact.get("registration_time") == fingerprint.get("registration_time")
    assert fact.get("uuid") == fingerprint.get("subscription_manager_id")
    if fact.get("hostname", "").endswith(
        tuple("-" + str(num) for num in range(1, 10))
    ) and fact.get("hostname").startswith("virt-who-"):
        assert "hypervisor" == fingerprint.get("infrastructure_type")
    else:
        assert "virtualized" == fingerprint.get("infrastructure_type")
    assert fact.get("cores") == fingerprint.get("cpu_core_count")
    assert fact.get("num_sockets") == fingerprint.get("cpu_socket_count")
    assert fact.get("architecture") == fingerprint.get("architecture")
    assert fact.get("is_redhat") == fingerprint.get("is_redhat")


def _create_network_fingerprint(server_id, fingerprint_task_runner, *args, **kwargs):
    """Create test network fingerprint."""
    network_details_report = _create_network_details_report_json(*args, **kwargs)
    network_fact = network_details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.NETWORK,
        "facts": network_details_report["facts"],
    }
    network_fingerprints = fingerprint_task_runner._process_source(source)
    network_fingerprint = network_fingerprints[0]
    _validate_network_result(network_fingerprint, network_fact)
    return network_fingerprint


def _create_vcenter_fingerprint(server_id, fingerprint_task_runner, *args, **kwargs):
    """Create test network/vcenter fingerprints."""
    v_details_report = _create_vcenter_details_report_json(*args, **kwargs)
    vfact = v_details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source2",
        "source_type": DataSources.VCENTER,
        "facts": v_details_report["facts"],
    }
    vfingerprints = fingerprint_task_runner._process_source(source)
    vfingerprint = vfingerprints[0]
    _validate_vcenter_result(vfingerprint, vfact)
    return vfingerprint


def _create_satellite_fingerprint(server_id, fingerprint_task_runner, *args, **kwargs):
    """Create test satellite fingerprints."""
    s_details_report = _create_satellite_details_report_json(*args, **kwargs)
    sfact = s_details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source3",
        "source_type": DataSources.SATELLITE,
        "facts": s_details_report["facts"],
    }
    sfingerprints = fingerprint_task_runner._process_source(source)
    sfingerprint = sfingerprints[0]
    _validate_satellite_result(sfingerprint, sfact)
    return sfingerprint


################################################################
# Test Source functions
################################################################
@pytest.mark.parametrize(
    "system_purpose_json",
    [
        None,
        {},
        {"_version": 1},
        {"_version": 1, "role": "server"},
        {"_version": 1, "role": "server", "service_level_agreement": "self-service"},
        {
            "_version": 1,
            "role": "server",
            "service_level_agreement": "self-service",
            "usage": "dev",
        },
        {
            "_version": 1,
            "role": "server",
            "service_level_agreement": "self-service",
            "usage": "dev",
            "addons": "ibm",
        },
        {
            "_version": 1,
            "role": "server",
            "service_level_agreement": "self-service",
            "usage": "dev",
            "addons": "ibm",
            "random_extra_field": "redhat",
        },
    ],
)
@pytest.mark.django_db
def test_process_network_source(
    server_id, fingerprint_task_runner, system_purpose_json
):
    """Test process network source based on various system purpose JSONs."""
    _create_network_fingerprint(
        server_id, fingerprint_task_runner, system_purpose_json=system_purpose_json
    )
    # We have no special assertions here because _create_network_fingerprint already
    # performs validation with assertions.


@pytest.mark.parametrize(
    "facts, expected_raw_fact_key, expected_infrastructure_type",
    (
        (
            {"virt_what_type": "bare metal"},
            "virt_what_type",
            SystemFingerprint.BARE_METAL,
        ),
        (
            {"virt_type": "unspecified-magic"},
            "virt_type",
            SystemFingerprint.VIRTUALIZED,
        ),
        (
            {"subman_virt_is_guest": True},
            "subman_virt_is_guest",
            SystemFingerprint.VIRTUALIZED,
        ),
        (
            {"virt_what_type": "unspecified-magic"},
            "virt_what_type",
            SystemFingerprint.UNKNOWN,
        ),
        (
            {"virt_what_type": None},
            "virt_what_type/virt_type",
            SystemFingerprint.UNKNOWN,
        ),
        ({}, "virt_what_type/virt_type", SystemFingerprint.UNKNOWN),
    ),
)
@pytest.mark.django_db
def test_process_network_source_infrastructure_type(
    server_id,
    fingerprint_task_runner,
    facts,
    expected_raw_fact_key,
    expected_infrastructure_type,
):
    """
    Test that network source fact processing gives expected infrastructure types.

    This test is intended to test exhaustively many inputs that can lead to the various
    infrastructure_type fingerprint values that could indicate a virtualized guest.
    """
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.NETWORK,
    }
    fingerprint = fingerprint_task_runner._process_network_fact(source, facts)
    assert fingerprint["infrastructure_type"] == expected_infrastructure_type
    assert (
        fingerprint[META_DATA_KEY]["infrastructure_type"]["raw_fact_key"]
        == expected_raw_fact_key
    )


@pytest.mark.django_db
def test_process_network_system_purpose(server_id, fingerprint_task_runner):
    """Test process network system_purpose."""
    system_purpose_json = {
        "_version": "1",
        "role": "server",
        "service_level_agreement": "self-support",
        "usage": "test",
        "addons": ["a", "b", "c"],
    }

    details_report = _create_network_details_report_json(
        system_purpose_json=system_purpose_json
    )
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.NETWORK,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_network_result(fingerprint, fact)


@pytest.mark.django_db
def test_process_vcenter_source_with_dns(server_id, fingerprint_task_runner):
    """Test process vcenter source that has a dns name."""
    details_report = _create_vcenter_details_report_json()
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.VCENTER,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_vcenter_result(fingerprint, fact)


@pytest.mark.django_db
def test_process_vcenter_source_no_dns_name(server_id, fingerprint_task_runner):
    """Test process vcenter source with no dns name."""
    details_report = _create_vcenter_details_report_json(
        report_id=1,
        source_name="source2",
        source_type=DataSources.VCENTER,
        vm_cpu_count=2,
        vm_os="RHEL 7.3",
        vm_mac_addresses=None,
        vm_ip_addresses=None,
        vm_name="TestMachine",
        vm_state="On",
        vm_uuid="a037f26f-2988-57bd-85d8-de7617a3aab0",
        vm_dns_name=None,
    )
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.VCENTER,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_vcenter_result(fingerprint, fact)


@pytest.mark.django_db
def test_process_satellite_source(server_id, fingerprint_task_runner):
    """Test process satellite source."""
    details_report = _create_satellite_details_report_json()
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.SATELLITE,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_satellite_result(fingerprint, fact)


@pytest.mark.django_db
def test_process_satellite_source_hypervisor(server_id, fingerprint_task_runner):
    """Test processing sat source for hypervisor infrastructure."""
    details_report = _create_satellite_details_report_json(
        report_id=1,
        source_name="source3",
        source_type=DataSources.SATELLITE,
        hostname="virt-who-9384389442-5",
    )
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.SATELLITE,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_satellite_result(fingerprint, fact)


@pytest.mark.django_db
def test_process_satellite_source_not_hypervisor(server_id, fingerprint_task_runner):
    """Test processing sat source for virtualized infrastructure."""
    details_report = _create_satellite_details_report_json(
        report_id=1,
        source_name="source3",
        source_type=DataSources.SATELLITE,
        hostname="virt-who-9384389442-0",
    )
    fact = details_report["facts"][0]
    source = {
        "server_id": server_id,
        "source_name": "source1",
        "source_type": DataSources.SATELLITE,
        "facts": details_report["facts"],
    }
    fingerprints = fingerprint_task_runner._process_source(source)
    fingerprint = fingerprints[0]
    _validate_satellite_result(fingerprint, fact)


################################################################
# Test merge functions
################################################################
@pytest.mark.django_db
def test_merge_network_and_vcenter(server_id, fingerprint_task_runner):
    """Test merge of two lists of fingerprints."""
    nfingerprints = [
        _create_network_fingerprint(
            server_id,
            fingerprint_task_runner,
            dmi_system_uuid="match",
            ifconfig_mac_addresses=["1"],
        ),
        _create_network_fingerprint(
            server_id,
            fingerprint_task_runner,
            dmi_system_uuid=1,
            ifconfig_mac_addresses=["2"],
        ),
    ]
    vfingerprints = [
        _create_vcenter_fingerprint(
            server_id, fingerprint_task_runner, vm_uuid="match"
        ),
        _create_vcenter_fingerprint(server_id, fingerprint_task_runner, vm_uuid=2),
    ]

    n_cpu_count = nfingerprints[0]["cpu_count"]
    v_cpu_count = vfingerprints[0]["cpu_count"]
    v_name = vfingerprints[0]["name"]
    assert n_cpu_count != v_cpu_count

    reverse_priority_keys = {"cpu_count"}
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_VCENTER_MERGE_KEYS,
        nfingerprints,
        vfingerprints,
        reverse_priority_keys=reverse_priority_keys,
    )
    assert len(result_fingerprints) == 3

    for result_fingerprint in result_fingerprints:
        if result_fingerprint.get("vm_uuid") == "match":
            assert result_fingerprint.get("cpu_count") == v_cpu_count
            assert result_fingerprint.get("cpu_count") != n_cpu_count
            assert result_fingerprint.get("name") != v_name


@pytest.mark.django_db
def test_merge_network_and_vcenter_infrastructure_type(
    server_id, fingerprint_task_runner
):
    """Test if VCenter infrastructure_type is prefered over network."""
    nfingerprints = [
        _create_network_fingerprint(
            server_id,
            fingerprint_task_runner,
            dmi_system_uuid="match",
            ifconfig_mac_addresses=["1"],
        )
    ]
    vfingerprints = [
        _create_vcenter_fingerprint(server_id, fingerprint_task_runner, vm_uuid="match")
    ]
    # change infrastructure_type to bypass the validation
    nfingerprints[0]["infrastructure_type"] = "unknown"
    vfingerprints[0]["infrastructure_type"] = "virtualized"
    assert (
        nfingerprints[0]["infrastructure_type"]
        != vfingerprints[0]["infrastructure_type"]
    )

    reverse_priority_keys = {"cpu_count", "infrastructure_type"}
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_VCENTER_MERGE_KEYS,
        nfingerprints,
        vfingerprints,
        reverse_priority_keys=reverse_priority_keys,
    )
    for result_fingerprint in result_fingerprints:
        if result_fingerprint.get("vm_uuid") == "match":
            assert result_fingerprint.get("infrastructure_type") == "virtualized"


@pytest.mark.django_db
def test_merge_mac_address_case_insensitive(server_id, fingerprint_task_runner):
    """Test if fingerprints will be merged with mixed mac addr."""
    n_mac = ["00:50:56:A3:A2:E8", "00:50:56:c3:d2:m8"]
    v_mac = ["00:50:56:a3:a2:e8", "00:50:56:C3:D2:m8"]
    s_mac = ["00:50:56:A3:a2:E8", "00:50:56:C3:D2:M8"]
    assert v_mac != n_mac
    assert v_mac != s_mac
    nfingerprints = [
        _create_network_fingerprint(
            server_id, fingerprint_task_runner, ifconfig_mac_addresses=n_mac
        )
    ]
    vfingerprints = [
        _create_vcenter_fingerprint(
            server_id, fingerprint_task_runner, vm_mac_addresses=v_mac
        )
    ]
    sfingerprints = [
        _create_satellite_fingerprint(
            server_id, fingerprint_task_runner, mac_addresses=s_mac
        )
    ]
    v_mac_addresses = vfingerprints[0]["mac_addresses"]
    n_mac_addresses = nfingerprints[0]["mac_addresses"]
    s_mac_addresses = sfingerprints[0]["mac_addresses"]
    assert v_mac_addresses == n_mac_addresses
    assert v_mac_addresses == s_mac_addresses
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
    )
    assert len(result_fingerprints) == 1
    reverse_priority_keys = {"cpu_count", "infrastructure_type"}
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_VCENTER_MERGE_KEYS,
        nfingerprints,
        vfingerprints,
        reverse_priority_keys=reverse_priority_keys,
    )
    assert len(result_fingerprints) == 1


@pytest.mark.django_db
def test_merge_net_sate_vcenter_infrastructure_type(server_id, fingerprint_task_runner):
    """Test if VCenter infrastructure_type is preferred over the others."""
    nfingerprints = [
        _create_network_fingerprint(
            server_id,
            fingerprint_task_runner,
            dmi_system_uuid="match",
            ifconfig_mac_addresses=["1"],
        )
    ]
    vfingerprints = [
        _create_vcenter_fingerprint(server_id, fingerprint_task_runner, vm_uuid="match")
    ]
    sfingerprints = [
        _create_satellite_fingerprint(server_id, fingerprint_task_runner, uuid="match")
    ]
    # change infrastructure_type to bypass the validation
    nfingerprints[0]["infrastructure_type"] = "unknown"
    sfingerprints[0]["infrastructure_type"] = "test"
    vfingerprints[0]["infrastructure_type"] = "virtualized"
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
    )
    for result_fingerprint in result_fingerprints:
        if result_fingerprint.get("vm_uuid") == "match":
            assert result_fingerprint.get("infrastructure_type") == "test"
    reverse_priority_keys = {"cpu_count", "infrastructure_type"}
    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_VCENTER_MERGE_KEYS,
        nfingerprints,
        vfingerprints,
        reverse_priority_keys=reverse_priority_keys,
    )
    for result_fingerprint in result_fingerprints:
        if result_fingerprint.get("vm_uuid") == "match":
            assert result_fingerprint.get("infrastructure_type") == "virtualized"


@pytest.mark.django_db
def test_merge_matching_fingerprints(fingerprint_task_runner):
    """Test merge of two lists of fingerprints."""
    nmetadata = {
        "os_release": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "raw_fact_key": "etc_release_release",
        },
        "bios_uuid": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "raw_fact_key": "dmi_system_uuid",
        },
    }
    nsources = {
        "source1": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
        }
    }
    nfingerprint_to_merge = {
        "id": 1,
        "os_release": "RHEL 7",
        "bios_uuid": "match",
        "metadata": nmetadata,
        "sources": nsources,
    }
    nfingerprint_no_match = {
        "id": 2,
        "os_release": "RHEL 7",
        "bios_uuid": "2345",
        "metadata": nmetadata,
        "sources": nsources,
    }
    nfingerprint_no_key = {
        "id": 3,
        "os_release": "RHEL 6",
        "metadata": nmetadata,
        "sources": nsources,
    }
    nfingerprints = [
        nfingerprint_to_merge,
        nfingerprint_no_match,
        nfingerprint_no_key,
    ]

    vmetadata = {
        "os_release": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "raw_fact_key": "etc_release_release",
        },
        "vm_uuid": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
            "raw_fact_key": "vm.uuid",
        },
    }
    vsources = {
        "source1": {
            "source_name": "source1",
            "source_type": DataSources.VCENTER,
        }
    }
    vfingerprint_to_merge = {
        "id": 5,
        "os_release": "Windows 7",
        "vm_uuid": "match",
        "metadata": vmetadata,
        "sources": vsources,
    }
    vfingerprint_no_match = {
        "id": 6,
        "os_release": "RHEL 7",
        "vm_uuid": "9876",
        "metadata": vmetadata,
        "sources": vsources,
    }
    vfingerprint_no_key = {
        "id": 7,
        "os_release": "RHEL 6",
        "metadata": vmetadata,
        "sources": vsources,
    }
    vfingerprints = [
        vfingerprint_to_merge,
        vfingerprint_no_match,
        vfingerprint_no_key,
    ]

    expected_merge_fingerprint = deepcopy(nfingerprint_to_merge)
    expected_merge_fingerprint["vm_uuid"] = "match"
    expected_merge_fingerprint["metadata"]["vm_uuid"] = vmetadata["vm_uuid"]

    (
        _,
        merge_list,
        no_match_found_list,
    ) = fingerprint_task_runner._merge_matching_fingerprints(
        "bios_uuid", nfingerprints, "vm_uuid", vfingerprints
    )
    merged_sources = {
        "source1": {
            "source_name": "source1",
            "source_type": DataSources.NETWORK,
        }
    }

    # merge list should always contain all nfingerprints (base_list)
    assert len(merge_list) == 3
    assert expected_merge_fingerprint in merge_list
    assert nfingerprint_no_match in merge_list
    assert nfingerprint_no_key in merge_list

    # assert VM property merged
    assert expected_merge_fingerprint.get("vm_uuid") is not None

    # assert network os_release had priority
    assert expected_merge_fingerprint.get("os_release") == "RHEL 7"
    assert expected_merge_fingerprint.get("sources") == merged_sources

    # assert those that didn't match, don't have VM properties
    assert nfingerprint_no_match.get("vm_uuid") is None
    assert nfingerprint_no_key.get("vm_uuid") is None

    # no_match_found list should only contain vfingerprints
    #  with no match
    assert len(no_match_found_list) == 2
    assert vfingerprint_no_match in no_match_found_list
    assert vfingerprint_no_key in no_match_found_list


@pytest.mark.django_db
def test_remove_duplicate_fingerprints(fingerprint_task_runner):
    """Test remove duplicate fingerprints created by index."""
    fingerprints = [
        {
            "id": 1,
            "os_release": "RHEL 7",
            "mac_addresses": ["1234", "2345"],
            "sources": [],
        },
        {
            "id": 2,
            "os_release": "RHEL 7",
            "mac_addresses": ["9876", "8765"],
            "sources": [],
        },
        {"id": 3, "os_release": "RHEL 6", "sources": []},
    ]
    index, no_key_found = fingerprint_task_runner._create_index_for_fingerprints(
        "mac_addresses", fingerprints
    )

    assert len(no_key_found) == 1
    assert no_key_found[0]["id"] == 3
    assert no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY) is not None
    assert len(index.keys()) == 4
    assert index.get("1234") is not None
    assert index.get("2345") is not None
    assert index.get("9876") is not None
    assert index.get("8765") is not None

    # deplicate but leave unique key
    leave_key_list = list(index.values())
    unique_list = fingerprint_task_runner._remove_duplicate_fingerprints(
        [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list
    )
    assert len(unique_list) == 2
    assert unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY) is not None

    # same test, but add value that doesn't have key
    leave_key_list = list(index.values())
    leave_key_list.append({"id": 3, "os_release": "RHEL 6"})
    unique_list = fingerprint_task_runner._remove_duplicate_fingerprints(
        [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list
    )
    assert len(unique_list) == 3

    # now pass flag to strip id key
    remove_key_list = list(index.values())
    unique_list = fingerprint_task_runner._remove_duplicate_fingerprints(
        [FINGERPRINT_GLOBAL_ID_KEY], remove_key_list, True
    )
    assert len(unique_list) == 2
    assert unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY) is None


@pytest.mark.django_db
def test_create_index_for_fingerprints(fingerprint_task_runner):
    """Test create index for fingerprints."""
    fingerprints = [
        {"id": 1, "os_release": "RHEL 7", "bios_uuid": "1234"},
        {"id": 2, "os_release": "RHEL 7", "bios_uuid": "2345"},
        {"id": 3, "os_release": "RHEL 6"},
    ]

    # Test that unique id not in objects
    index, no_key_found = fingerprint_task_runner._create_index_for_fingerprints(
        "bios_uuid", fingerprints, False
    )
    assert no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY) is None

    # Tests with unique id in objects
    index, no_key_found = fingerprint_task_runner._create_index_for_fingerprints(
        "bios_uuid", fingerprints
    )

    assert len(no_key_found) == 1
    assert no_key_found[0]["id"] == 3
    assert no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY) is not None
    assert len(index.keys()) == 2
    assert index.get("1234") is not None
    assert index.get("2345") is not None


@pytest.mark.django_db
def test_merge_fingerprint(server_id, fingerprint_task_runner):
    """Test merging a vcenter and network fingerprint."""
    nfingerprint = _create_network_fingerprint(server_id, fingerprint_task_runner)
    vfingerprint = _create_vcenter_fingerprint(server_id, fingerprint_task_runner)

    assert nfingerprint.get("vm_state") is None
    assert nfingerprint.get("vm_uuid") is None
    assert nfingerprint.get("vm_dns_name") is None
    assert nfingerprint.get("vm_host_socket_count") is None
    assert nfingerprint.get("vm_datacenter") is None
    assert nfingerprint.get("vm_cluster") is None

    assert vfingerprint.get("os_name") is None
    assert vfingerprint.get("os_version") is None
    assert vfingerprint.get("bios_uuid") is None
    assert vfingerprint.get("subscription_manager_id") is None
    assert vfingerprint.get("cpu_socket_count") is None
    assert vfingerprint.get("cpu_core_count") is None

    merged_fingerprint = fingerprint_task_runner._merge_fingerprint(
        nfingerprint, vfingerprint
    )

    assert merged_fingerprint.get("vm_state") is not None
    assert merged_fingerprint.get("vm_uuid") is not None
    assert merged_fingerprint.get("vm_dns_name") is not None
    assert merged_fingerprint.get("vm_host_socket_count") is not None
    assert merged_fingerprint.get("vm_datacenter") is not None
    assert merged_fingerprint.get("vm_cluster") is not None

    assert merged_fingerprint.get("name") is not None
    assert merged_fingerprint.get("os_name") is not None
    assert merged_fingerprint.get("os_version") is not None
    assert merged_fingerprint.get("bios_uuid") is not None
    assert merged_fingerprint.get("subscription_manager_id") is not None
    assert merged_fingerprint.get("cpu_socket_count") is not None
    assert merged_fingerprint.get("cpu_core_count") is not None


def assert_all_fingerprints_have_sudo(metadata_dict):
    """
    Check if all fingerprints have 'has_sudo' set to True.

    If not all are True, all offending fingerprints will appear on the error log.
    """
    # fp <<< abbreviation for fingerprint
    assert all(fp_meta["has_sudo"] for fp_meta in metadata_dict.values()), [
        fp_name for fp_name, fp_meta in metadata_dict.items() if not fp_meta["has_sudo"]
    ]


def test_assert_all_fingerprints_have_sudo():
    """Test assert_all_fingerprints_have_sudo."""
    fake_fingerprints = {"foo": {"has_sudo": True}, "bar": {"has_sudo": True}}
    assert_all_fingerprints_have_sudo(fake_fingerprints)
    fake_fingerprints["foo"]["has_sudo"] = False
    with pytest.raises(AssertionError) as exception_info:
        assert_all_fingerprints_have_sudo(fake_fingerprints)
    assert "['foo']" in str(exception_info.value)


@pytest.mark.django_db
def test_merge_fingerprint_sudo(server_id, fingerprint_task_runner):
    """Test merging two network one sudo and one without."""
    # Test that sudo is preferred when part of priority fingerprint
    sudo_fingerprint = _create_network_fingerprint(server_id, fingerprint_task_runner)
    sudo_fingerprint["products"] = []
    sudo_fingerprint["entitlements"] = []

    regular_fingerprint = _create_network_fingerprint(
        server_id, fingerprint_task_runner, user_has_sudo=False
    )
    regular_fingerprint["products"] = []
    regular_fingerprint["entitlements"] = []

    result = fingerprint_task_runner._merge_fingerprint(
        sudo_fingerprint, regular_fingerprint
    )
    assert result == sudo_fingerprint
    assert_all_fingerprints_have_sudo(result["metadata"])

    # Test that sudo is preferred when part of to merge fingerprint
    sudo_fingerprint = _create_network_fingerprint(server_id, fingerprint_task_runner)
    sudo_fingerprint["products"] = []
    sudo_fingerprint["entitlements"] = []

    regular_fingerprint = _create_network_fingerprint(
        server_id, fingerprint_task_runner, user_has_sudo=False
    )
    regular_fingerprint["products"] = []
    regular_fingerprint["entitlements"] = []

    result = fingerprint_task_runner._merge_fingerprint(
        regular_fingerprint, sudo_fingerprint
    )
    assert_all_fingerprints_have_sudo(result["metadata"])


@pytest.mark.django_db
def test_merge_fingerprint_network_win(server_id, fingerprint_task_runner):
    """Test merge of fingerprint prioritizes network values."""
    nfingerprint = _create_network_fingerprint(server_id, fingerprint_task_runner)
    vfingerprint = _create_vcenter_fingerprint(server_id, fingerprint_task_runner)

    nfingerprint["os_release"] = "Fedora"
    assert vfingerprint.get("os_release") != nfingerprint["os_release"]

    new_fingerprint = fingerprint_task_runner._merge_fingerprint(
        nfingerprint, vfingerprint
    )

    assert new_fingerprint.get("os_release") == nfingerprint["os_release"]


@pytest.mark.django_db
def test_source_name_in_metadata(server_id, source, fingerprint_task_runner):
    """Test that adding facts includes source_name in metadata."""
    sourcetopass = {
        "server_id": server_id,
        "source_name": source.name,
        "source_type": source.source_type,
    }
    fingerprint = {"metadata": {}}
    result = fingerprint_task_runner._process_network_fact(sourcetopass, fingerprint)
    assert result["metadata"]["infrastructure_type"]["source_name"] == "source1"


@pytest.mark.django_db
def test_all_facts_with_null_value_in_process_network_scan(
    server_id, source, fingerprint_task_runner
):
    """Test fingerprinting method with all facts set to null value."""
    source_dict = {
        "server_id": server_id,
        "source_name": source.name,
        "source_type": source.source_type,
    }
    facts_dict = network_template()
    result = fingerprint_task_runner._process_network_fact(source_dict, facts_dict)
    metadata_dict = result.pop(META_DATA_KEY)

    expected_metadata = {
        fingerprint_name: {
            "server_id": server_id,
            "source_name": source.name,
            "source_type": source.source_type,
            "has_sudo": None,
            "raw_fact_key": fact_name,
        }
        for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_NETWORK.items()
    }
    # Two slight changes from the default EXPECTED_FINGERPRINT_MAP_NETWORK dict:
    # This test creates facts_dict with None for all facts, and when we fingerprint,
    # if ifconfig_ip_addresses is None, we switch from ifconfig_ip_addresses to
    # ip_address_show_ipv4 as the raw fact source for ip_addresses. The same logic
    # applies for mac_addresses. Other tests that set not-None values in these raw
    # facts continue to expect the default ifconfig-related raw fact names.
    expected_metadata["ip_addresses"]["raw_fact_key"] = "ip_address_show_ipv4"
    expected_metadata["mac_addresses"]["raw_fact_key"] = "ip_address_show_mac"

    assert set(metadata_dict.keys()) == set(EXPECTED_FINGERPRINT_MAP_NETWORK.keys())
    assert expected_metadata == metadata_dict

    expected_fingerprints = {
        fingerprint_name: None for fingerprint_name in EXPECTED_FINGERPRINT_MAP_NETWORK
    }
    expected_fingerprints[PRODUCTS_KEY] = mock.ANY
    expected_fingerprints[ENTITLEMENTS_KEY] = []
    expected_fingerprints["infrastructure_type"] = SystemFingerprint.UNKNOWN
    assert result == expected_fingerprints


@pytest.mark.django_db
def test_scan_all_facts_with_null_value_in_process_vcenter_scan(
    server_id, fingerprint_task_runner
):
    """Test fingerprinting method with all facts set to null value."""
    source_dict = {
        "server_id": server_id,
        "source_name": "source2",
        "source_type": DataSources.VCENTER,
    }
    facts_dict = vcenter_template()
    result = fingerprint_task_runner._process_vcenter_fact(source_dict, facts_dict)
    metadata_dict = result.pop(META_DATA_KEY)
    assert set(metadata_dict.keys()) == set(EXPECTED_FINGERPRINT_MAP_VCENTER.keys())
    assert {
        fingerprint_name: {
            "server_id": server_id,
            "source_name": "source2",
            "source_type": DataSources.VCENTER,
            "has_sudo": False,
            "raw_fact_key": fact_name,
        }
        for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_VCENTER.items()
    } == metadata_dict

    expected_fingerprints = {
        fingerprint_name: None for fingerprint_name in EXPECTED_FINGERPRINT_MAP_VCENTER
    }
    expected_fingerprints["is_redhat"] = False
    expected_fingerprints["infrastructure_type"] = SystemFingerprint.VIRTUALIZED
    expected_fingerprints[PRODUCTS_KEY] = []
    expected_fingerprints[ENTITLEMENTS_KEY] = []
    assert result == expected_fingerprints


@pytest.mark.django_db
def test_scan_all_facts_with_null_value_in_process_satellite_scan(
    server_id, fingerprint_task_runner
):
    """Test fingerprinting method with all facts set to null value."""
    source_dict = {
        "server_id": server_id,
        "source_name": "source3",
        "source_type": DataSources.SATELLITE,
    }
    facts_dict = satellite_template()
    result = fingerprint_task_runner._process_satellite_fact(source_dict, facts_dict)
    metadata_dict = result.pop(META_DATA_KEY)

    assert set(metadata_dict.keys()) == set(EXPECTED_FINGERPRINT_MAP_SATELLITE.keys())
    assert {
        fingerprint_name: {
            "server_id": server_id,
            "source_name": "source3",
            "source_type": DataSources.SATELLITE,
            "has_sudo": False,
            "raw_fact_key": fact_name,
        }
        for fingerprint_name, fact_name in EXPECTED_FINGERPRINT_MAP_SATELLITE.items()
    } == metadata_dict

    expected_fingerprints = {
        fingerprint_name: None
        for fingerprint_name in EXPECTED_FINGERPRINT_MAP_SATELLITE
    }
    expected_fingerprints["is_redhat"] = False
    expected_fingerprints["infrastructure_type"] = SystemFingerprint.UNKNOWN
    expected_fingerprints[ENTITLEMENTS_KEY] = []

    copy_products_list = deepcopy(PRODUCTS)
    for product in copy_products_list:
        product["metadata"] = {
            "server_id": server_id,
            "source_name": "source3",
            "source_type": "satellite",
            "raw_fact_key": None,
        }
    expected_fingerprints[PRODUCTS_KEY] = copy_products_list
    assert result == expected_fingerprints


################################################################
# Test post processing
################################################################
@pytest.mark.django_db
def test_compute_system_creation_time(server_id, fingerprint_task_runner):
    """Test merge of two lists of fingerprints."""
    nfingerprints = [
        _create_network_fingerprint(
            server_id,
            fingerprint_task_runner,
            ifconfig_mac_addresses=["1"],
            date_machine_id="2018-3-7",
        )
    ]
    sfingerprints = [
        _create_satellite_fingerprint(
            server_id, fingerprint_task_runner, mac_addresses=["1"]
        )
    ]

    (
        _,
        result_fingerprints,
    ) = fingerprint_task_runner._merge_fingerprints_from_source_types(
        NETWORK_SATELLITE_MERGE_KEYS, nfingerprints, sfingerprints
    )
    assert len(result_fingerprints) == 1
    rfp = result_fingerprints[0]
    rfp["date_yum_history"] = "2018-1-7"
    rfp["date_filesystem_create"] = None
    rfp["date_anaconda_log"] = "201837"
    rfp["registration_time"] = "2018-4-7 12:45:02"
    rfp["date_machine_id"] = None
    fingerprint_task_runner._compute_system_creation_time(rfp)
    test_date = datetime.strptime("2018-4-7", "%Y-%m-%d").date()

    assert rfp["system_creation_date"] == test_date
    metadata = rfp["metadata"]["system_creation_date"]["raw_fact_key"]
    assert "registration_time" == metadata


################################################################
# Test multi_format_dateparse
################################################################
@pytest.mark.django_db
def test_multi_format_dateparse(fingerprint_task_runner):
    """Test multi_format_dateparse with various formats."""
    source = {"source_type": "network", "source_name": "test_source"}
    test_date = datetime.strptime("2018-4-7", "%Y-%m-%d").date()
    date_value = fingerprint_task_runner._multi_format_dateparse(
        source,
        "fake_key",
        "2018-4-7 12:45:02",
        ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"],
    )
    assert date_value == test_date

    date_value = fingerprint_task_runner._multi_format_dateparse(
        source,
        "fake_key",
        "2018-4-7 12:45:02 -0400",
        ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"],
    )
    assert date_value == test_date

    date_value = fingerprint_task_runner._multi_format_dateparse(
        source, "fake_key", "2018-4-7 12:45:02 -0400", ["%Y-%m-%d %H:%M:%S"]
    )
    assert date_value is None


@pytest.mark.django_db
def test_process_details_report_failed(fingerprint_task_runner):
    """Test processing a details report no valid fps."""
    fact_collection = {}
    deployments_report = DeploymentsReport()
    report = Report(deployment_report=deployments_report)
    with patch(
        "fingerprinter.runner.FingerprintTaskRunner._process_sources",
        return_value=fact_collection,
    ):
        status_message, status = fingerprint_task_runner._process_details_report(
            "", report
        )
        assert "failed" in status_message.lower()
        assert status == "failed"


@pytest.mark.django_db
def test_process_details_report_success(fingerprint_task_runner):
    """Test processing a details report success."""
    fact_collection = {
        "name": "dhcp181-3.gsslab.rdu2.redhat.com",
        "metadata": {},
        "etc_machine_id": "3f01b55457674041b75e41829bcee1dc",
        "insights_client_id": "3f01b55457674041b75e41829bcee1dc",
        "ip_addresses": ["1.2.3.4"],
        "sources": [],
    }
    deployments_report = DeploymentsReport(id=1)
    deployments_report.save()
    report = Report(id=1, deployment_report=deployments_report)
    with patch(
        "fingerprinter.runner.FingerprintTaskRunner._process_sources",
        return_value=[fact_collection],
    ):
        status_message, status = fingerprint_task_runner._process_details_report(
            "", report
        )
    assert "success" in status_message.lower()
    assert status == "completed"


@pytest.mark.django_db
def test_process_details_report_exception(fingerprint_task_runner):
    """Test processing a details report with an exception."""
    fact_collection = {
        "name": "dhcp181-3.gsslab.rdu2.redhat.com",
        "metadata": {},
        "sources": [],
    }
    deployments_report = DeploymentsReport(id=1)
    deployments_report.save()
    report = Report(id=1, deployment_report=deployments_report)
    with (
        patch(
            "fingerprinter.runner.FingerprintTaskRunner._process_sources",
            return_value=[fact_collection],
        ),
        patch(
            "fingerprinter.runner.SystemFingerprintSerializer.save",
            side_effect=DataError,
        ),
    ):
        status_message, status = fingerprint_task_runner._process_details_report(
            "", report
        )
        assert "failed" in status_message.lower()
        assert status == "failed"


@pytest.mark.parametrize(
    "certs, expected_formatted_certs",
    [
        (["69.pem", "67.pem", ""], [69, 67]),
        ([], []),  # assert empty list stays empty
        (["notint.pem"], []),  # assert exception returns empty
    ],
)
def test_format_certs(certs, expected_formatted_certs):
    """Testing the format_certs function."""
    assert expected_formatted_certs == FingerprintTaskRunner.format_certs(certs)
