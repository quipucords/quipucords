"""Test source serializer."""

import pytest
from django.core.exceptions import ValidationError

from api import messages
from api.models import Credential, Source
from api.source.serializer import SourceSerializer, SourceSerializerV2
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


SINGLE_HOST_SOURCE_TYPES = [
    DataSources.VCENTER,
    DataSources.SATELLITE,
    DataSources.OPENSHIFT,
    DataSources.RHACS,
    DataSources.ANSIBLE,
]


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


@pytest.fixture
def openshift_source_with_false_ssl(openshift_cred_id):
    """Openshift source with ssl_cert_verify=False."""
    source = Source.objects.create(
        name="source_saved_false_ssl",
        source_type=DataSources.OPENSHIFT,
        port=222,
        hosts=["1.2.3.4"],
        ssl_cert_verify=False,
    )
    source.credentials.add(openshift_cred_id)
    source.save()
    return source


@pytest.mark.django_db
@pytest.mark.parametrize(
    "hosts_input",
    [
        ["192.0.2.0/30"],
        ["192.0.2.5/32"],
        ["192.0.2.128/31"],
        ["192.168.1.8/29"],
        ["10.0.0.0/24"],
        ["fd00:cafe:babe::/120"],
        ["192.0.2.0/30", "10.0.0.0/24"],
        ["192.0.2.0/30", "192.168.1.[1:3]"],
        ["192.168.1.1", "10.0.0.0/24"],
    ],
)
def test_cidr_preserved(network_cred_id, hosts_input):
    """Test CIDR blocks are preserved as-is (not expanded) in the serializer."""
    data = {
        "name": "source",
        "source_type": DataSources.NETWORK,
        "hosts": hosts_input,
        "credentials": [network_cred_id],
    }

    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data.get("hosts") == hosts_input


@pytest.mark.django_db
@pytest.mark.parametrize(
    "hosts_input",
    [
        ["192.168.1.[1:3]"],
        ["10.0.[5:6].1"],
        ["192.168.[0:1].[1:2]"],
        ["host[1:5].example.com"],
        ["192.168.1.[1:3]", "10.0.[5:6].1"],
        ["192.168.1.1", "192.168.1.[1:3]"],
    ],
)
def test_ansible_range_preserved(network_cred_id, hosts_input):
    """Test Ansible-style ranges are preserved as-is in the serializer."""
    data = {
        "name": "source",
        "source_type": DataSources.NETWORK,
        "hosts": hosts_input,
        "credentials": [network_cred_id],
    }

    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data.get("hosts") == hosts_input


def _create_credential_for_source_type(source_type):
    """Create a credential matching the given source type."""
    if source_type in (DataSources.VCENTER, DataSources.SATELLITE):
        return Credential.objects.create(
            name=f"{source_type}_cred",
            cred_type=source_type,
            username=f"{source_type}_user",
            password=f"{source_type}_password",
        )
    else:
        return Credential.objects.create(
            name=f"{source_type}_cred",
            cred_type=source_type,
            auth_token=f"{source_type}_token",
        )


@pytest.mark.django_db
@pytest.mark.parametrize("source_type", SINGLE_HOST_SOURCE_TYPES)
@pytest.mark.parametrize(
    "hosts_input",
    [
        "192.0.2.0/30",
        "10.0.0.0/24",
        "fd00:cafe:babe::/120",
    ],
)
def test_single_host_source_rejects_cidr(source_type, hosts_input):
    """Single-host sources should reject CIDR notation and raise SOURCE_ONE_HOST."""
    credential = _create_credential_for_source_type(source_type)
    data = {
        "name": "single-host source",
        "source_type": source_type,
        "hosts": [hosts_input],
        "credentials": [credential.id],
    }

    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "hosts" in serializer.errors
    assert messages.SOURCE_ONE_HOST in serializer.errors["hosts"]


@pytest.mark.django_db
@pytest.mark.parametrize("source_type", SINGLE_HOST_SOURCE_TYPES)
@pytest.mark.parametrize(
    "hosts_input",
    [
        "192.0.2.[1:10]",
        "10.0.0.[5:15]",
    ],
)
def test_single_host_source_rejects_ansible_range(source_type, hosts_input):
    """Single-host sources should reject Ansible-style ranges."""
    credential = _create_credential_for_source_type(source_type)
    data = {
        "name": "single-host source",
        "source_type": source_type,
        "hosts": [hosts_input],
        "credentials": [credential.id],
    }

    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "hosts" in serializer.errors
    assert messages.SOURCE_ONE_HOST in serializer.errors["hosts"]


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
        ("192.168.1.0/30", ["192.168.1.0/30"]),
        ("10.0.0.0/29", ["10.0.0.0/29"]),
        ("example.com", ["example.com"]),
        ("sub.example.org", ["sub.example.org"]),
        ("10.0.[5:6].1", ["10.0.[5:6].1"]),
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


@pytest.mark.parametrize(
    "proxy_url",
    [
        "http://proxy.example.com:8080",
        "https://localhost:3128",
        "http://127.0.0.1:8000",
    ],
)
def test_valid_proxy_url_formats(proxy_url):
    """Test valid proxy URLs with proper schema and port."""
    SourceSerializerV2.is_valid_proxy_url_format(proxy_url)


@pytest.mark.parametrize(
    "proxy_url",
    [
        pytest.param("proxy:port", marks=pytest.mark.xfail(strict=True)),
        pytest.param("", marks=pytest.mark.xfail(strict=True)),
        pytest.param(None, marks=pytest.mark.xfail(strict=True)),
        pytest.param("proxy.example.com:8080", marks=pytest.mark.xfail(strict=True)),
        pytest.param(
            "ftp://proxy.example.com:21", marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param("proxy.example.com", marks=pytest.mark.xfail(strict=True)),
        pytest.param("8080", marks=pytest.mark.xfail(strict=True)),
        pytest.param("proxy@:8080", marks=pytest.mark.xfail(strict=True)),
        pytest.param("http://:8080", marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_invalid_proxy_url_formats(proxy_url):
    """Test proxy URLs expected to fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        SourceSerializerV2.is_valid_proxy_url_format(proxy_url)
    assert "Enter a valid proxy URL" in str(exc_info.value.detail[0])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "proxy_url",
    [
        "http://proxy.example.com:8080",
        "https://localhost:3128",
        "http://127.0.0.1:8000",
        "http://192.168.0.1:8080",
        "https://sub.domain.example.com:9999",
        None,
        pytest.param("", marks=pytest.mark.xfail(strict=True)),
        pytest.param(
            "ftp://proxy.example.com:21", marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param("proxy:port", marks=pytest.mark.xfail(strict=True)),
        pytest.param("proxy.example.com", marks=pytest.mark.xfail(strict=True)),
        pytest.param("8080", marks=pytest.mark.xfail(strict=True)),
        pytest.param("proxy@:8080", marks=pytest.mark.xfail(strict=True)),
        pytest.param("http://:8080", marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_validate_proxy_url(openshift_cred_id, proxy_url):
    """Test proxy URL validation considering format."""
    data = {
        "name": "source",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "proxy_url": proxy_url,
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    if proxy_url:
        assert serializer.validated_data["proxy_url"] == proxy_url


@pytest.mark.parametrize("port", [None, 0, 65536, 8080])
def test_validate_port_valid_values(port):
    """Test that valid ports pass validation."""
    assert SourceSerializer.validate_port(port) == port


@pytest.mark.parametrize(
    "port,expected_msg",
    [
        pytest.param(
            -1, messages.NET_INVALID_PORT, marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param(
            65537, messages.NET_INVALID_PORT, marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param(
            "8080", messages.INVALID_PORT, marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param("", messages.INVALID_PORT, marks=pytest.mark.xfail(strict=True)),
        pytest.param([], messages.INVALID_PORT, marks=pytest.mark.xfail(strict=True)),
        pytest.param({}, messages.INVALID_PORT, marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_validate_port_invalid_values(port, expected_msg):
    """Test that invalid ports raise ValidationError with the correct message."""
    with pytest.raises(ValidationError) as exc_info:
        SourceSerializer.validate_port(port)

    assert str(exc_info.value.detail[0]) == expected_msg


@pytest.mark.django_db
def test_ssl_cert_verify_defaults_true_when_ssl_fields_absent(openshift_cred_id):
    """Ensure ssl_cert_verify defaults to True when all SSL fields are omitted."""
    data = {
        "name": "ssl-default-no-fields",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is True
    assert instance.ssl_protocol is None
    assert instance.disable_ssl is None
    assert instance.use_paramiko is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ssl_field, value",
    [
        ("ssl_protocol", "TLSv1_2"),
        ("disable_ssl", True),
        ("disable_ssl", False),
    ],
)
def test_ssl_cert_verify_defaults_true_with_other_ssl_field(
    openshift_cred_id, ssl_field, value
):
    """Ensure ssl_cert_verify defaults to True when other SSL field is provided."""
    data = {
        "name": f"ssl-default-{ssl_field}-{value}",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        ssl_field: value,
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is True, (
        "ssl_cert_verify should default to True for HTTP sources "
        "when not explicitly provided, even if other SSL fields are set."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("ssl_cert_verify_value", [True, False])
def test_explicit_ssl_cert_verify_sets_only_itself(
    openshift_cred_id, ssl_cert_verify_value
):
    """Ensure only ssl_cert_verify is set when provided; SSL fields remain None."""
    data = {
        "name": f"ssl-cert-only-{ssl_cert_verify_value}",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_cert_verify": ssl_cert_verify_value,
        # No other SSL fields
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify == ssl_cert_verify_value
    assert instance.ssl_protocol is None
    assert instance.disable_ssl is None
    assert instance.use_paramiko is None


@pytest.mark.django_db
@pytest.mark.parametrize("ssl_cert_verify_value", [True, False])
@pytest.mark.parametrize(
    "other_ssl_field, other_value",
    [
        ("disable_ssl", True),
        ("ssl_protocol", "TLSv1_2"),
    ],
)
def test_ssl_cert_verify_respected_when_combined_with_other_ssl_fields(
    openshift_cred_id, ssl_cert_verify_value, other_ssl_field, other_value
):
    """Test that ssl_cert_verify is preserved when combined with other SSL fields."""
    data = {
        "name": f"ssl-combo-{ssl_cert_verify_value}-{other_ssl_field}-{other_value}",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_cert_verify": ssl_cert_verify_value,
        other_ssl_field: other_value,
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    # Assert ssl_cert_verify is preserved
    assert instance.ssl_cert_verify == ssl_cert_verify_value

    # Assert the other SSL field is set
    assert getattr(instance, other_ssl_field) == other_value

    # Assert all remaining SSL fields are None
    for field in {"ssl_protocol", "disable_ssl", "use_paramiko"} - {other_ssl_field}:
        assert getattr(instance, field) is None


@pytest.mark.django_db
@pytest.mark.parametrize("use_paramiko_value", [True, False])
def test_network_source_ssl_fields(network_cred_id, use_paramiko_value):
    """Ensure only use_paramiko is populated for network sources; others remain None."""
    data = {
        "name": f"network-paramiko-{use_paramiko_value}",
        "source_type": DataSources.NETWORK,
        "hosts": ["10.0.0.1"],
        "credentials": [network_cred_id],
        "use_paramiko": use_paramiko_value,
    }

    serializer = SourceSerializerV2(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.use_paramiko == use_paramiko_value
    assert instance.ssl_cert_verify is None
    assert instance.ssl_protocol is None
    assert instance.disable_ssl is None


@pytest.mark.django_db
def test_ssl_cert_verify_defaults_to_true_on_update(
    openshift_source, openshift_cred_id
):
    """If ssl_cert_verify was True and is omitted in update, it remains True."""
    assert openshift_source.ssl_cert_verify is True

    update_data = {
        "name": "ssl-update-test",
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_protocol": "TLSv1_1",  # Changing an SSL field
        # Intentionally omitting ssl_cert_verify
    }

    serializer = SourceSerializerV2(data=update_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is True, (
        "ssl_cert_verify should remain True when not explicitly updated, "
        "even if other SSL fields are provided."
    )


@pytest.mark.django_db
def test_update_explicitly_sets_ssl_cert_verify_false_from_true(
    openshift_source, openshift_cred_id
):
    """Update explicitly sets ssl_cert_verify from True to False."""
    update_data = {
        "name": "ssl-update-to-false",
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_cert_verify": False,
    }

    serializer = SourceSerializerV2(data=update_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is False


@pytest.mark.django_db
def test_ssl_cert_verify_false_is_preserved_on_update(
    openshift_source_with_false_ssl, openshift_cred_id
):
    """Ensure ssl_cert_verify=False is preserved on update when not explicitly set."""
    update_data = {
        "name": "ssl-update-false-preserved",
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_protocol": "TLSv1_2",
    }

    serializer = SourceSerializerV2(
        data=update_data, instance=openshift_source_with_false_ssl
    )
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is False


@pytest.mark.django_db
def test_ssl_cert_verify_false_to_true(
    openshift_source_with_false_ssl, openshift_cred_id
):
    """Update explicitly sets ssl_cert_verify from False to True."""
    update_data = {
        "name": "ssl-update-to-true",
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "ssl_cert_verify": True,
    }

    serializer = SourceSerializerV2(
        data=update_data, instance=openshift_source_with_false_ssl
    )
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is True


@pytest.mark.django_db
def test_ssl_cert_verify_true_is_preserved_on_update(
    openshift_source, openshift_cred_id
):
    """Ensure ssl_cert_verify=True is preserved when not explicitly set."""
    update_data = {
        "name": "ssl-update-true-preserved",
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
        "disable_ssl": False,
    }

    serializer = SourceSerializerV2(data=update_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.ssl_cert_verify is True
