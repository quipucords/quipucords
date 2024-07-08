"""test network scan normalizer."""

import pytest

from api.deployments_report.model import SystemFingerprint
from scanner.network.normalizer import (
    Normalizer,
    infrastructure_type_normalizer,
    ip_address_normalizer,
)
from tests.utils import raw_facts_generator
from tests.utils.raw_facts_generator import fake_virt_what


@pytest.fixture
def raw_facts():
    """Return raw facts for testing."""
    raw_facts_list = list(raw_facts_generator("network", 1))
    facts = raw_facts_list[0]
    facts["virt_type"] = "some-vendor"
    facts["virt_what"] = fake_virt_what(["potato-computer"], 0)
    return facts


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
        "system_purpose": raw_facts["system_purpose_json"],
        "infrastructure_type": "virtualized",
        "infrastructure_vendor": "some-vendor",
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


@pytest.mark.parametrize(
    "facts, expected_value, expected_raw_fact_keys",
    (
        (  # non-empty virt_what trumps anything else
            {
                "virt_what": {"value": ["potato"]},  # "virtual" I guess
                "subman_virt_is_guest": False,  # unknown
                "hostnamectl": {"value": {"chassis": "desktop"}},  # physical
            },
            SystemFingerprint.VIRTUALIZED,
            ["virt_what"],
        ),
        (  # prefer subman_virt_is_guest True over hostnamectl
            {
                "virt_what": None,  # unknown
                "subman_virt_is_guest": True,  # virtual
                "hostnamectl": {"value": {"chassis": "desktop"}},  # physical
            },
            SystemFingerprint.VIRTUALIZED,
            ["subman_virt_is_guest"],
        ),
        (  # subman_virt_is_guest not-True is ignored, leaving hostnamectl
            {
                "subman_virt_is_guest": False,  # unknown
                "hostnamectl": {"value": {"chassis": "vm"}},  # virtual
            },
            SystemFingerprint.VIRTUALIZED,
            ["hostnamectl"],
        ),
        (  # mystery hostnamectl values are treated as physical
            {
                "hostnamectl": {"value": {"chassis": "potato"}},  # physical
            },
            SystemFingerprint.BARE_METAL,
            ["hostnamectl"],
        ),
        (  # if all are missing or empty, infra is truly unknown
            {
                "virt_what": None,
                "subman_virt_is_guest": None,
                "hostnamectl": None,
            },
            SystemFingerprint.UNKNOWN,
            ["virt_what"],
        ),
        (  # alternate inputs for unknown
            {
                "virt_what": {"value": []},
                "hostnamectl": {"value": {"foo": "bar"}},
                # ignore non-chassis values
            },
            SystemFingerprint.UNKNOWN,
            ["virt_what"],
        ),
    ),
)
def test_infrastructure_type_normalizer(facts, expected_value, expected_raw_fact_keys):
    """
    Test infrastructure_type_normalizer.

    IMPORTANT DEVELOPER NOTE: This test's implementation largely duplicates the code
    originally written in test_process_network_source_infrastructure_type.

    TODO FIXME: Remove duplicate code when we switch to the new normalizers.
    """
    norm_result = infrastructure_type_normalizer(**facts)
    assert norm_result.value == expected_value
    assert norm_result.raw_fact_keys == expected_raw_fact_keys


class TestIPAddressNormalizer:
    """Test ip_address_normalizer."""

    def test_ipv4_and_ipv6(self, faker):
        """Test ipv4 and ipv6."""
        ipv4 = faker.ipv4()
        ipv6 = faker.ipv6()
        result = ip_address_normalizer([ipv4, ipv6])
        assert result == [ipv4]

    def test_error(self, faker):
        """Test ip_address_normalizer error."""
        ipv4 = faker.ipv4()
        non_ip = faker.slug()
        with pytest.raises(ValueError):
            ip_address_normalizer([ipv4, non_ip])

    @pytest.mark.parametrize("input", [None, []])
    def test_empty(self, input):
        """Test empty input."""
        assert ip_address_normalizer(input) == []
