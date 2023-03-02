"""Test the product eap."""

import unittest

from django.test import TestCase

# pylint: disable=wrong-import-order
from api.models import ServerInformation  # noqa
from fingerprinter.jboss_eap import (
    detect_jboss_eap,
    verify_classification,
    version_aware_dedup,
)


class TestVersionAwareDedup(unittest.TestCase):
    """Test the version aware dedup."""

    def test_dedup(self):
        """Dedup redundant version numbers."""
        self.assertEqual(version_aware_dedup(["1", "1.0", "1.0.1"]), {"1.0.1"})

    def test_empty_input(self):
        """Return an empty set for an empty input."""
        self.assertEqual(version_aware_dedup([]), set())


class ProductEAPTest(TestCase):
    """Tests Product EAP class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retrieve_server_id()

    def test_detect_jboss_eap_present(self):
        """Test the detect_jboss_eap method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "eap_home_ls": {"opt/eap6/": ["jboss-modules.jar"]},
            "jboss_eap_jar_ver": [
                {"version": "1.3.6.Final-redhat-1", "date": "2018-01-18"}
            ],
        }
        product = detect_jboss_eap(source, facts)
        expected = {
            "name": "JBoss EAP",
            "presence": "present",
            "version": ["6.4.0"],
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "eap_home_ls/jboss_eap_jar_ver",
            },
        }
        self.assertEqual(product, expected)

    # pylint: disable=C0103
    def test_detect_jboss_eap_potential_common(self):
        """Test the detect_jboss_eap method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"jboss_eap_common_files": ["jboss-modules.jar"]}
        product = detect_jboss_eap(source, facts)
        expected = {
            "name": "JBoss EAP",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "jboss_eap_common_files",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_potential_sub(self):
        """Test the detect_jboss_eap method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"subman_consumed": [{"name": "JBoss EAP Sub"}]}
        product = detect_jboss_eap(source, facts)
        expected = {
            "name": "JBoss EAP",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "subman_consumed",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_potential_ent(self):
        """Test the detect_jboss_eap method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "JBoss EAP Sub"}]}
        product = detect_jboss_eap(source, facts)
        expected = {
            "name": "JBoss EAP",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": "entitlements",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_absent(self):
        """Test the detect_jboss_eap method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "Satellite Sub"}]}
        product = detect_jboss_eap(source, facts)
        expected = {
            "name": "JBoss EAP",
            "presence": "absent",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": None,
            },
        }
        self.assertEqual(product, expected)


class TestVerifyClassification(unittest.TestCase):
    """Test the classification verification."""

    def test_wildfly(self):
        """Test that a wildfly version returns False."""
        self.assertEqual(verify_classification("WildFly-10"), False)

    def test_jbossas(self):
        """Test that a jbossas version returns False."""
        self.assertEqual(verify_classification("JBossAS-7"), False)

    def test_eap(self):
        """Test that an eap version returns True."""
        self.assertEqual(verify_classification("6.0.1"), True)
