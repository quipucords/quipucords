"""test network scan normalizer."""


import pytest

from scanner.network.normalizer import Normalizer


@pytest.fixture
def raw_facts(faker):
    """Return raw facts for testing."""
    return {
        "cloud_provider": "aws",
        "cpu_core_count": 4,
        "cpu_core_per_socket": "1",
        "cpu_count": "4",
        "cpu_hyperthreading": False,
        "cpu_socket_count": 4,
        "dmi_system_uuid": faker.uuid4(),
        "etc_machine_id": faker.uuid4(),
        "etc_release_release": "Red Hat Enterprise Linux release 8.6 (Ootpa)",
        "ifconfig_ip_addresses": [faker.ipv4()],
        "ifconfig_mac_addresses": [faker.mac_address()],
        "insights_client_id": faker.uuid4(),
        "subscription_manager_id": faker.uuid4(),
        "system_memory_bytes": "16691544064",
        "system_purpose_json": None,
        "uname_processor": "x86_64",
        "virt_type": "vmware",
        "virt_virt": "virt-guest",
        "virt_what_type": "vmware",
    }


@pytest.fixture
def expected_normalized_facts(raw_facts):
    """Return normalized facts."""
    return {
        "mac_addresses": raw_facts["ifconfig_mac_addresses"],
        "ip_addresses": raw_facts["ifconfig_ip_addresses"],
        "bios_uuid": raw_facts["dmi_system_uuid"],
        "insights_id": raw_facts["insights_client_id"],
        "subscription_manager_id": raw_facts["subscription_manager_id"],
        "number_of_cpus": int(raw_facts["cpu_core_count"]),
        "number_of_sockets": int(raw_facts["cpu_socket_count"]),
        "cores_per_socket": int(raw_facts["cpu_core_per_socket"]),
        "system_memory_bytes": int(raw_facts["system_memory_bytes"]),
        "os_release": raw_facts["etc_release_release"],
        "arch": raw_facts["uname_processor"],
        "cloud_provider": raw_facts["cloud_provider"],
        "system_purpose": None,
        "infrastructure_type": "virtualized",
        "network_interfaces": [
            {
                "ipv4_addresses": raw_facts["ifconfig_ip_addresses"],
                "ipv6_addresses": [],
                "name": "unknown",
            }
        ],
        "etc_machine_id": raw_facts["etc_machine_id"],
    }


def test_normalizer(mocker, raw_facts, expected_normalized_facts):
    """Test normalization "greenpath"."""
    norm = Normalizer(raw_facts, mocker.ANY)
    norm.normalize()
    assert norm.facts == expected_normalized_facts


def test_invalid_number_of_cpus(mocker):
    """This is an example on how to indirectly test system profile validation."""
    # cpu_core_count for this test is way bigger then the value accepted for
    # number_of_cpus on system profile
    raw_facts = {"cpu_core_count": 42_000_000_000}
    n = Normalizer(raw_facts, mocker.ANY)
    n.normalize()
    n.facts["number_of_cpus"] is None
