"""Test the product brms."""

from django.test import TestCase

from api.models import ServerInformation
from fingerprinter.jboss_brms import detect_jboss_brms


class ProductBRMSTest(TestCase):
    """Tests Product BRMS class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retrieve_server_id()

    def test_detect_jboss_brms_present(self):
        """Test the detect_jboss_brms method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "jboss_brms_manifest_mf": {("/opt/brms", "6.4.0.Final-redhat-3")},
            "jboss_brms_kie_api_ver": {("/opt/brms", "6.4.0.Final-redhat-3")},
        }
        product = detect_jboss_brms(source, facts)
        expected = {
            "name": "JBoss BRMS",
            "presence": "present",
            "version": ["BRMS 6.3.0"],
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "jboss_brms_kie_api_ver/" "jboss_brms_manifest_mf",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_brms_potential_sub(self):
        """Test the detect_jboss_brms method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"subman_consumed": [{"name": "JBoss BRMS Sub"}]}
        product = detect_jboss_brms(source, facts)
        expected = {
            "name": "JBoss BRMS",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "subman_consumed",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_brms_potential_ent(self):
        """Test the detect_jboss_brms method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "JBoss BRMS Sub"}]}
        product = detect_jboss_brms(source, facts)
        expected = {
            "name": "JBoss BRMS",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": "entitlements",
            },
        }
        self.assertEqual(product, expected)

    def test_detect_jboss_brms_absent(self):
        """Test the detect_jboss_brms method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "Satellite Sub"}]}
        product = detect_jboss_brms(source, facts)
        expected = {
            "name": "JBoss BRMS",
            "presence": "absent",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": None,
            },
        }
        self.assertEqual(product, expected)
