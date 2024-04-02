"""Test the network scanner utility functions."""

import unittest
from unittest import mock

from scanner.network import utils


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
