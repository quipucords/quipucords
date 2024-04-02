"""Unit tests for initial processing of ifconfig facts."""

import unittest

from scanner.network.processing import ifconfig
from scanner.network.processing.util_for_test import ansible_result


class TestProcessIPAddresses(unittest.TestCase):
    """Test ProcessIPAddresses."""

    def test_success_case(self):
        """Found IP."""
        self.assertEqual(
            ifconfig.ProcessIPAddresses.process(ansible_result("inet addr: 1.2.3.4")),
            ["1.2.3.4"],
        )

    def test_not_found(self):
        """Did not find IP."""
        self.assertEqual(ifconfig.ProcessIPAddresses.process(ansible_result("")), [])


class TestProcessMacAddresses(unittest.TestCase):
    """Test ProcessMacAddresses."""

    def test_success_case(self):
        """Found mac address."""
        self.assertEqual(
            ifconfig.ProcessMacAddresses.process(ansible_result("00:10:20:3a:40:b5")),
            ["00:10:20:3a:40:b5"],
        )

    def test_not_found(self):
        """Did not find mac address."""
        self.assertEqual(ifconfig.ProcessMacAddresses.process(ansible_result("")), [])
