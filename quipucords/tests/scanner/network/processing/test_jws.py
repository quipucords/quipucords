"""Unit tests for initial processing."""

import unittest

from scanner.network.processing import jws
from tests.scanner.network.processing.util_for_test import ansible_result


class TestProcessJWSInstalledWithRpm(unittest.TestCase):
    """Test ProcessJWSInstalledWithRpm."""

    def test_installed_with_rpm(self):
        """Return true if jws was installed with rpm."""
        self.assertEqual(
            jws.ProcessJWSInstalledWithRpm.process(
                ansible_result("Red Hat JBoss Web Server")
            ),
            True,
        )

    def test_not_installed_with_rpm(self):
        """Return false if jws was not installed with rpm."""
        self.assertEqual(
            jws.ProcessJWSInstalledWithRpm.process(ansible_result("Not installed")),
            False,
        )


class TestProcessHasJBossEula(unittest.TestCase):
    """Test ProcessHasJBossEULA."""

    def test_has_eula_file(self):
        """Return true if jboss eula file exists."""
        self.assertEqual(jws.ProcessHasJBossEULA.process(ansible_result("true")), True)

    def test_has_no_eula_file(self):
        """Return false if jboss eula file does not exist."""
        self.assertEqual(
            jws.ProcessHasJBossEULA.process(ansible_result("false")), False
        )


class TestProcessJWSHasCert(unittest.TestCase):
    """Test ProcessJWSHasCert."""

    def test_true(self):
        """Return True if /etc/pki/product/185.pem exists."""
        self.assertEqual(
            jws.ProcessJWSHasCert.process(ansible_result("/etc/pki/product/185.pem")),
            True,
        )

    def test_false(self):
        """Return False if /etc/pki/product/185.pem does not exist."""
        self.assertEqual(jws.ProcessJWSHasCert.process(ansible_result("")), False)
