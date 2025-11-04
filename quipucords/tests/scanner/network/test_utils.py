"""Test the network scanner utility functions."""

import unittest
from pathlib import Path
from unittest import mock

import pytest
from django.forms import model_to_dict

from api import vault
from api.serializers import SourceSerializer
from constants import GENERATED_SSH_KEYFILE, DataSources
from scanner.network import utils
from tests.factories import CredentialFactory, SourceFactory


@pytest.mark.django_db
def test_scan_inventory_with_valid_ssh_key(
    network_credential, network_host_addresses, faker
):
    """Test construct_inventory returns dict with valid path to the SSH key."""
    with network_credential.generate_ssh_keyfile() as ssh_keypath:
        cred_data = model_to_dict(network_credential)
        cred_data[GENERATED_SSH_KEYFILE] = ssh_keypath
        # network_host_addresses[0] because it has only one address by default.
        host_address = network_host_addresses[0]
        _, inventory_dict = utils.construct_inventory(
            [(host_address, cred_data)],
            connection_port=faker.pyint(),
            concurrency_count=faker.pyint(),
        )

        ssh_keyfile = inventory_dict["all"]["children"]["group_0"]["hosts"][
            host_address
        ]["ansible_ssh_private_key_file"]
        assert Path(ssh_keyfile).exists()
    # check context manager cleanup
    assert not Path(ssh_keyfile).exists()


@pytest.mark.django_db
def test_construct_inventory_from_source_and_credential_models(faker):
    """Test construct_inventory using data from full Source and Credential objects."""
    # TODO Simplify this test. Does this really need to use full model objects?
    # We are not directly mimicking runtime behaviors here, and this test's general
    # implementation is an historic artifact from a previous version of tests.
    # Maybe we should just define the inputs to `utils.construct_inventory` directly
    # and avoid the (seemingly useless) overhead of instantiating the models.

    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        password=faker.password(),
        become_password=faker.password(),
        become_user=faker.slug(),
    )
    source = SourceFactory(
        source_type=DataSources.NETWORK,
        credentials=[credential],
        port=faker.pyint(),
        hosts=[faker.ipv4_private()],
    )
    serializer = SourceSerializer(source)
    source_data = serializer.data
    credential_data = model_to_dict(credential)

    expected = {
        "all": {
            "children": {
                "group_0": {
                    "hosts": {source.hosts[0]: {"ansible_host": source.hosts[0]}}
                }
            },
            "vars": {
                "ansible_port": source.port,
                "ansible_user": credential.username,
                "ansible_ssh_pass": vault.decrypt_data_as_unicode(credential.password),
                "ansible_become_pass": vault.decrypt_data_as_unicode(
                    credential.become_password
                ),
                "ansible_become_method": credential.become_method,
                "ansible_become_user": credential.become_user,
            },
        }
    }

    _, inventory_dict = utils.construct_inventory(
        hosts=source_data["hosts"],
        credential=credential_data,
        connection_port=source_data["port"],
        concurrency_count=1,
    )
    assert inventory_dict == expected


# TODO Convert this TestCase class to plain pytest test functions.
class TestConstructVars(unittest.TestCase):
    """Test _construct_vars."""

    @mock.patch("scanner.network.utils.decrypt_data_as_unicode")
    def test_construct_vars(self, decrypt_data):
        """Test constructing ansible vars dictionary."""
        decrypt_data.side_effect = lambda x: x
        vars_dict = utils._construct_vars(
            22,
            {
                "name": "cred1",
                "username": "username",
                "password": "password",
                "become_password": "sudo",
                "ssh_keyfile": "keyfile",
                "become_method": "sudo",
                "become_user": "root",
            },
        )
        expected = {
            "ansible_become_pass": "sudo",
            "ansible_port": 22,
            "ansible_ssh_pass": "password",
            "ansible_ssh_private_key_file": "keyfile",
            "ansible_user": "username",
            "ansible_become_user": "root",
            "ansible_become_method": "sudo",
        }
        self.assertEqual(vars_dict, expected)


# TODO Convert this TestCase class to plain pytest test functions.
class TestExpandHostpattern(unittest.TestCase):
    """Test utils.expand_hostpattern."""

    def test_single_hostname(self):
        """A single hostname."""
        self.assertEqual(utils.expand_hostpattern("domain.com"), ["domain.com"])

    def test_single_hostname_with_port(self):
        """Users can specify a port, too."""
        self.assertEqual(utils.expand_hostpattern("domain.com:1234"), ["domain.com"])

    def test_hostname_range(self):
        """A range of hostnames."""
        self.assertEqual(
            utils.expand_hostpattern("[a:c].domain.com"),
            ["a.domain.com", "b.domain.com", "c.domain.com"],
        )

    def test_single_ip_address(self):
        """A single IP address."""
        self.assertEqual(utils.expand_hostpattern("1.2.3.4"), ["1.2.3.4"])

    def test_ip_range(self):
        """A range of IP addresses."""
        self.assertEqual(
            utils.expand_hostpattern("1.2.3.[4:6]"), ["1.2.3.4", "1.2.3.5", "1.2.3.6"]
        )


def test_raw_facts_template():
    """Ensure raw facts template only caches fact names, not values."""
    # any netscan raw fact is good for testing this. just choosing one easy to remember.
    fact = "cpu_count"
    template = utils.raw_facts_template()
    assert template[fact] is None
    template[fact] = 1
    assert utils.raw_facts_template()[fact] is None


def test_is_valid_ipv4_address():
    """Test is_valid_ipv4_address."""
    assert utils.is_valid_ipv4_address("1.2.3.4")
    assert utils.is_valid_ipv4_address("127.0.0.1")
    assert not utils.is_valid_ipv4_address("bad.one")


def test_is_valid_ipv6_address():
    """Test is_valid_ipv6_address."""
    assert utils.is_valid_ipv6_address("1aee:69c2:717c:93c2:402:7f62:863:1b6a")
    assert utils.is_valid_ipv6_address("::1")
    assert not utils.is_valid_ipv6_address("bad::one")


def test_get_ipv4_ipv6_addresses():
    """Test get_ipv4_ipv6_addresses."""
    ipv4_addresses, ipv6_addresses = utils.get_ipv4_ipv6_addresses(
        [
            "127.0.0.1",
            "bad.one",
            "4f5f:dd5:cfde:3d41:578d:63dc:9101:a928",
            "::1",
            "192.168.99.99",
            "bad:one:",
        ]
    )
    assert set(ipv4_addresses) == {"127.0.0.1", "192.168.99.99"}
    assert set(ipv6_addresses) == {"4f5f:dd5:cfde:3d41:578d:63dc:9101:a928", "::1"}
