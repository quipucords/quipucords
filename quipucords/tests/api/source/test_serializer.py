"""Test source serializer."""

import ipaddress

import pytest
from django.core.exceptions import ValidationError

from api import messages
from api.models import Credential, Source
from api.source.serializer import SourceSerializer
from constants import DataSources


@pytest.fixture
def network_cred_id():
    """Return network credential."""
    network_credential = Credential.objects.create(
        name="network_cred",
        cred_type=DataSources.NETWORK,
        username="username",
        password="password",
    )
    return network_credential.id


@pytest.fixture
def openshift_cred_id():
    """Return openshift credential."""
    openshift_credential = Credential.objects.create(
        name="openshift_cred",
        cred_type=DataSources.OPENSHIFT,
        auth_token="openshift_token",
    )
    return openshift_credential.id


@pytest.fixture
def satellite_cred_id():
    """Return satellite credential."""
    satellite_credential = Credential.objects.create(
        name="sat_cred",
        cred_type=DataSources.SATELLITE,
        username="satellite_user",
        password="satellite_password",
        become_password=None,
        ssh_keyfile=None,
    )
    return satellite_credential.id


@pytest.fixture
def openshift_source(openshift_cred_id):
    """Openshift Source."""
    source = Source.objects.create(
        name="source_saved",
        source_type=DataSources.OPENSHIFT,
        port=222,
        hosts=["1.2.3.4"],
        ssl_cert_verify=True,
    )
    source.credentials.add(openshift_cred_id)
    source.save()
    return source


@pytest.mark.django_db
@pytest.mark.parametrize(
    "hosts_input,expected_hosts",
    [
        ("192.0.2.0/30", ["192.0.2.1", "192.0.2.2"]),
        ("192.0.2.5/32", ["192.0.2.5"]),
        ("192.0.2.128/31", ["192.0.2.128", "192.0.2.129"]),
        (
            "192.168.1.8/29",
            [
                "192.168.1.9",
                "192.168.1.10",
                "192.168.1.11",
                "192.168.1.12",
                "192.168.1.13",
                "192.168.1.14",
            ],
        ),
        (
            "10.0.0.0/24",
            [str(ip) for ip in ipaddress.ip_network("10.0.0.0/24").hosts()],
        ),
    ],
)
def test_cidr_expansion(network_cred_id, hosts_input, expected_hosts):
    """Test CIDR blocks are expanded into individual IP addresses."""
    data = {
        "name": "source",
        "source_type": DataSources.NETWORK,
        "hosts": [hosts_input],
        "credentials": [network_cred_id],
    }

    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert set(serializer.validated_data.get("hosts")) == set(expected_hosts)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ansible_input,expected_hosts",
    [
        ("192.168.1.[1:3]", ["192.168.1.1", "192.168.1.2", "192.168.1.3"]),
        ("10.0.[5:6].1", ["10.0.5.1", "10.0.6.1"]),
        (
            "192.168.[0:1].[1:2]",
            ["192.168.0.1", "192.168.0.2", "192.168.1.1", "192.168.1.2"],
        ),
        pytest.param("192.168.[1000:1002].1", [], marks=pytest.mark.xfail(strict=True)),
        pytest.param("10.0.[5:3].1", [], marks=pytest.mark.xfail(strict=True)),
        pytest.param("10.0.[1:99999].1", [], marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_ansible_range_normalization(network_cred_id, ansible_input, expected_hosts):
    """Test Ansible-style ranges that resemble IP addresses."""
    data = {
        "name": "source",
        "source_type": DataSources.NETWORK,
        "hosts": [ansible_input],
        "credentials": [network_cred_id],
    }

    serializer = SourceSerializer(data=data)

    if expected_hosts:
        assert serializer.is_valid()
        assert set(serializer.validated_data.get("hosts")) == set(expected_hosts)
    else:
        assert not serializer.is_valid()


@pytest.mark.parametrize(
    "host,expected_result",
    [
        ("192.168.1.1", True),
        ("10.0.0.1", True),
        ("127.0.0.1", True),
        ("2001:db8:85a3::8a2e:370:7334", True),
        ("::1", True),
        ("256.256.256.256", False),  # Out of range
        ("192.168.1.", False),  # Trailing dot
        ("192.168..1.1", False),  # Double dots
        ("2001:db8:::1", False),  # Too many colons
        ("2001:db8:85a3:0:0:8a2e:370:g", False),  # Invalid hex digit
        ("", False),  # Empty string
    ],
)
def test_is_valid_ip(host, expected_result):
    """Test representative samples for IPv4 and IPv6 validation."""
    assert SourceSerializer.is_valid_ip(host) == expected_result


@pytest.mark.parametrize(
    "cidr,expected_result",
    [
        ("192.168.1.0/24", True),
        ("10.0.0.0/8", True),
        ("2001:db8::/32", True),
        ("::/128", True),
        ("192.168.1.0/33", False),  # Invalid prefix length
        ("2001:db8::/129", False),  # Out of range prefix
        ("::g/64", False),  # Invalid character in IPv6
        ("", False),  # Empty string
    ],
)
def test_is_valid_cidr(cidr, expected_result):
    """Test representative samples for IPv4 and IPv6 CIDR validation."""
    assert SourceSerializer.is_valid_cidr(cidr) == expected_result


@pytest.mark.parametrize(
    "hostname,expected_result",
    [
        ("example.com", True),
        ("Example.COM", True),
        ("localhost", False),
        ("sub.example.com", True),
        ("my-server.example.org", True),
        ("123.example.net", True),
        ("-invalid.com", False),  # Starts with a hyphen
        ("invalid-.com", False),  # Ends with a hyphen
        ("sub_domain.example.com", False),  # Contains an underscore
        ("exa mple.com", False),  # Contains a space
        ("!invalid.com", False),  # Special character
        ("example..com", False),  # Double dot
        ("a" * 254, False),  # Exceeds 253 characters
        ("", False),  # Empty string
    ],
)
def test_is_valid_hostname(hostname, expected_result):
    """Test FQDN hostname validation."""
    assert SourceSerializer.is_valid_hostname(hostname) == expected_result


@pytest.mark.parametrize(
    "host,expected_result",
    [
        ("host[1:3]", True),
        ("server[01:10]", True),
        ("web[5:9].example.com", True),
        ("host[1-3]", False),
        ("server[01:10:2]", False),
        ("web[a:z].example.com", False),
        ("10.0.[1:3].1", True),
        ("host[1:3].sub[4:5]", True),
        ("server1", False),  # No brackets
        ("", False),  # Empty string
        (None, False),  # None input
        ("host[:]", False),  # Missing numbers
    ],
)
def test_is_valid_ansible_range(host, expected_result):
    """Test if a string matches an Ansible-style range pattern."""
    assert SourceSerializer.is_valid_ansible_range(host) == expected_result


@pytest.mark.parametrize(
    "address,expected_output",
    [
        ("192.168.1.1", ["192.168.1.1"]),
        ("2001:db8::1", ["2001:db8::1"]),
        ("192.168.1.0/30", ["192.168.1.1", "192.168.1.2"]),
        (
            "10.0.0.0/29",
            ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5", "10.0.0.6"],
        ),
        ("example.com", ["example.com"]),
        ("sub.example.org", ["sub.example.org"]),
        ("10.0.[5:6].1", ["10.0.5.1", "10.0.6.1"]),
        pytest.param("invalid_host$", [], marks=pytest.mark.xfail(strict=True)),
        pytest.param(
            "256.256.256.256", [], marks=pytest.mark.xfail(strict=True)
        ),  # Invalid IP
        pytest.param(
            "192.168.1.0/33", [], marks=pytest.mark.xfail(strict=True)
        ),  # Invalid CIDR
        pytest.param(
            "host[1-3]", [], marks=pytest.mark.xfail(strict=True)
        ),  # Invalid Ansible range format
    ],
)
def test_classify_and_validate_address(address, expected_output):
    """Test classifying and validating different address types."""
    if expected_output:
        assert (
            SourceSerializer.classify_and_validate_address(address) == expected_output
        )
    else:
        with pytest.raises(ValidationError):
            SourceSerializer.classify_and_validate_address(address)


@pytest.mark.django_db
def test_unknown_source_type(openshift_cred_id):
    """Test if serializer is invalid when passing unknown source type."""
    data = {
        "name": "source1",
        "source_type": "test_source_type",
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "source_type" in serializer.errors


@pytest.mark.django_db
def test_wrong_cred_type(satellite_cred_id):
    """Test if serializer is invalid when passing inappropriate cred type."""
    error_message = messages.SOURCE_CRED_WRONG_TYPE
    data = {
        "name": "source2",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [satellite_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "source_type" in serializer.errors
    assert error_message in serializer.errors["source_type"]


@pytest.mark.django_db
def test_openshift_source_green_path(openshift_cred_id):
    """Test if serializer is valid when passing mandatory fields."""
    data = {
        "name": "source3",
        "source_type": DataSources.OPENSHIFT,
        "port": 222,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    source: Source = serializer.save()
    assert source.port == 222
    assert source.hosts == ["1.2.3.4"]
    assert source.ssl_cert_verify


@pytest.mark.django_db
def test_openshift_source_default_port(openshift_cred_id):
    """Test if serializer is valid when not passing port field."""
    data = {
        "name": "source3",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["port"] == 6443


@pytest.mark.skip(
    "The code being tested is broken. '5.4.3.2.1' should not be a valid host address. "
    "See also: https://issues.redhat.com/browse/DISCOVERY-352"
)
@pytest.mark.django_db
def test_openshift_source_update(openshift_source, openshift_cred_id):
    """Test if serializer updates fields correctly."""
    assert openshift_source.credentials
    updated_data = {
        "name": "source_updated",
        "hosts": ["5.4.3.2.1"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=updated_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert openshift_source.name == "source_updated"
    assert openshift_source.source_type == DataSources.OPENSHIFT


@pytest.mark.django_db
def test_openshift_source_update_options(openshift_source, openshift_cred_id):
    """Test if serializer updates fields correctly when options are present."""
    assert openshift_source.ssl_cert_verify
    updated_data = {
        "name": "source_updated",
        "hosts": ["5.4.3.2"],
        "options": {"ssl_cert_verify": False},
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=updated_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert openshift_source.name == "source_updated"
    assert openshift_source.source_type == DataSources.OPENSHIFT
    assert not openshift_source.ssl_cert_verify
