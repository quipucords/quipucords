"""Test the product JBoss Web Server."""

from unittest.mock import patch

from django.test import TestCase

# pylint: disable=wrong-import-order
from api.models import ServerInformation
from fingerprinter.jboss_web_server import detect_jboss_ws, get_version


class ProductJWSTest(TestCase):
    """Tests Product JWS class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retrieve_server_id()

    def test_get_version(self):
        """Test the get_version method."""
        raw_versions = ["JWS_3.0.3", "Not a version"]
        versions = get_version(raw_versions)
        expected = ["JWS 3.0.3"]

        self.assertEqual(versions, expected)

    # pylint: disable=unused-argument
    def test_detect_ws_present(self):
        """Test the detect_jboss_ws method."""
        expected = {
            "name": "JBoss Web Server",
            "presence": "present",
            "version": [],
            "metadata": {
                "raw_fact_key": "jws_installed_with_rpm",
                "source_name": "source1",
                "source_type": "network",
                "server_id": self.server_id,
            },
        }

        # Test where jws was installed with rpm
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"jws_installed_with_rpm": True}
        product = detect_jboss_ws(source, facts)
        self.assertEqual(product, expected)

        # Test where jws certificate was found
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"jws_installed_with_rpm": False, "jws_has_cert": True}
        expected["metadata"]["raw_fact_key"] = "jws_has_cert"
        product = detect_jboss_ws(source, facts)
        self.assertEqual(product, expected)

        # Test where valid version string is found
        facts = {
            "jws_installed_with_rpm": False,
            "jws_has_cert": False,
            "jws_version": "JWS_3.0.1",
        }
        expected["version"] = ["JWS 3.0.1"]
        expected["metadata"]["raw_fact_key"] = "jws_version"
        with patch(
            "fingerprinter.jboss_web_server.get_version", return_value=["JWS 3.0.1"]
        ):
            product = detect_jboss_ws(source, facts)
            self.assertEqual(product, expected)

    # pylint: disable=unused-argument
    def test_detect_ws_potential(self):
        """Test the detect_jboss_ws method."""
        expected = {
            "name": "JBoss Web Server",
            "presence": "potential",
            "version": [],
            "metadata": {
                "raw_fact_key": "tomcat_is_part_of_redhat_product",
                "source_name": "source1",
                "source_type": "network",
                "server_id": self.server_id,
            },
        }

        # Test where tomcat is part of red hat product
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "jws_has_eula_txt_file": False,
            "jws_installed_with_rpm": False,
            "tomcat_is_part_of_redhat_product": True,
        }
        product = detect_jboss_ws(source, facts)
        self.assertEqual(product, expected)

        # Test where JWS_HOME contains jboss eula file
        facts["tomcat_is_part_of_redhat_product"] = False
        facts["jws_has_eula_txt_file"] = True
        product = detect_jboss_ws(source, facts)
        expected["metadata"]["raw_fact_key"] = "jws_has_eula_txt_file"
        self.assertEqual(product, expected)

        # Test where server only has JWS entitlement
        facts["jws_has_eula_txt_file"] = False
        expected["metadata"]["raw_fact_key"] = None
        with patch(
            "fingerprinter.jboss_web_server.product_entitlement_found",
            return_value=True,
        ):
            product = detect_jboss_ws(source, facts)
            self.assertEqual(product, expected)

        # Test where only valid EWS version is found
        expected["version"] = ["EWS 1.0.0"]
        with patch(
            "fingerprinter.jboss_web_server.get_version", return_value=["EWS 1.0.0"]
        ):
            product = detect_jboss_ws(source, facts)
            self.assertEqual(product, expected)

    # pylint: disable=unused-argument
    def test_detect_ws_absent(self):
        """Test the detect_jboss_ws method."""
        # Test where tomcat is part of red hat product
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "jboss_has_eula_txt_file": False,
            "jws_installed_with_rpm": False,
            "tomcat_is_part_of_redhat_product": False,
        }
        expected = {
            "name": "JBoss Web Server",
            "presence": "absent",
            "version": [],
            "metadata": {
                "raw_fact_key": None,
                "source_name": "source1",
                "source_type": "network",
                "server_id": self.server_id,
            },
        }
        product = detect_jboss_ws(source, facts)
        self.assertEqual(product, expected)
