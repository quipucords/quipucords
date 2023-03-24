"""Unit tests for initial processing."""

# pylint: disable=missing-docstring

import unittest

from scanner.network.processing import jws
from scanner.network.processing.util_for_test import ansible_result


class TestProcessJWSInstalledWithRpm(unittest.TestCase):
    """Test ProcessJWSInstalledWithRpm."""

    def test_installed_with_rpm(self):
        """Return true if jws was installed with rpm."""
        assert (
            jws.ProcessJWSInstalledWithRpm.process(
                ansible_result("Red Hat JBoss Web Server")
            )
            is True
        )

    def test_not_installed_with_rpm(self):
        """Return false if jws was not installed with rpm."""
        assert (
            jws.ProcessJWSInstalledWithRpm.process(ansible_result("Not installed"))
            is False
        )


class TestProcessHasJBossEula(unittest.TestCase):
    """Test ProcessHasJBossEULA."""

    def test_has_eula_file(self):
        """Return true if jboss eula file exists."""
        assert jws.ProcessHasJBossEULA.process(ansible_result("true")) is True

    def test_has_no_eula_file(self):
        """Return false if jboss eula file does not exist."""
        assert jws.ProcessHasJBossEULA.process(ansible_result("false")) is False


class TestProcessTomcatPartOfRedhatProduct(unittest.TestCase):
    """Test ProcessTomcatPartOfRedhatProduct."""

    def test_true(self):
        """Return True if tomcat was installed as part of a redhat product."""
        assert (
            jws.ProcessTomcatPartOfRedhatProduct.process(ansible_result("True")) is True
        )

    def test_false(self):
        """Return False if tomcat is not part of a redhat product."""
        assert (
            jws.ProcessTomcatPartOfRedhatProduct.process(ansible_result("False"))
            is False
        )


class TestProcessJWSHasCert(unittest.TestCase):
    """Test ProcessJWSHasCert."""

    def test_true(self):
        """Return True if /etc/pki/product/185.pem exists."""
        assert (
            jws.ProcessJWSHasCert.process(ansible_result("/etc/pki/product/185.pem"))
            is True
        )

    def test_false(self):
        """Return False if /etc/pki/product/185.pem does not exist."""
        assert jws.ProcessJWSHasCert.process(ansible_result("")) is False
