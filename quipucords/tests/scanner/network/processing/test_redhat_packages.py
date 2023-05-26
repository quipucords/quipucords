"""Unit tests for initial processing."""


import unittest

from scanner.network.processing import redhat_packages
from scanner.network.processing.util_for_test import ansible_result, ansible_results


class TestProcessRedHatPackagesCerts(unittest.TestCase):
    """Test ProcessRedHatPackagesCerts."""

    def test_multiple_pems(self):
        """Return stdout with no trailing ;."""
        in_line = "69.pem;183.pem;"
        expected = "69.pem;183.pem"
        self.assertEqual(
            redhat_packages.ProcessRedHatPackagesCerts.process(ansible_result(in_line)),
            expected,
        )

    def test_no_pems_found(self):
        """Return empty string if it is given."""
        in_line = ""
        expected = ""
        self.assertEqual(
            redhat_packages.ProcessRedHatPackagesCerts.process(ansible_result(in_line)),
            expected,
        )

    def test_single_pem(self):
        """Return stdout with no trailing ;."""
        in_line = "69.pem;"
        expected = "69.pem"
        self.assertEqual(
            redhat_packages.ProcessRedHatPackagesCerts.process(ansible_result(in_line)),
            expected,
        )

    def test_ansible_error(self):
        """Did not find pem (empty string should be returned)."""
        self.assertEqual(
            redhat_packages.ProcessRedHatPackagesCerts.process(
                ansible_results([{"stdout": "", "rc": 1}])
            ),
            "",
        )
