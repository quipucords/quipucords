"""Test the product fuse."""


from django.test import TestCase

from api.models import ServerInformation
from fingerprinter.jboss_fuse import detect_jboss_fuse, get_version


class ProductFuseTest(TestCase):
    """Tests Product Fuse class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retrieve_server_id()

    def test_detect_jboss_fuse_present(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "eap_home_bin": {"opt/fuse/": ["jboss-fuse.jar"]},
            "jboss_activemq_ver": ["redhat-630187"],
        }
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "present",
            "version": ["Fuse-6.3.0"],
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "eap_home_bin/jboss_activemq_ver",
            },
        }
        assert product == expected

    # pylint: disable=C0103
    def test_detect_jboss_fuse_potential_init(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"jboss_fuse_systemctl_unit_files": ["jboss_fuse_init"]}
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "jboss_fuse_systemctl_unit_files",
            },
        }
        assert product == expected

    def test_detect_jboss_fuse_potential_sub(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {"subman_consumed": [{"name": "JBoss Fuse Sub"}]}
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "subman_consumed",
            },
        }
        assert product == expected

    def test_detect_jboss_fuse_potential_ent(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "JBoss Fuse Sub"}]}
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "potential",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": "entitlements",
            },
        }
        assert product == expected

    def test_detect_jboss_fuse_absent(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "satellite",
        }
        facts = {"entitlements": [{"name": "Satellite Sub"}]}
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "absent",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "satellite",
                "raw_fact_key": None,
            },
        }
        assert product == expected

    def test_detect_fuse_present(self):
        """Test the detect_jboss_fuse method."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "eap_home_bin": {"opt/fuse/": ["jboss-fuse.jar"]},
            "fuse_camel_version": ["redhat-630187"],
            "jboss_fuse_on_eap_activemq_ver": [
                {"homedir": "/foo/bin", "version": ["redhat-630187"]}
            ],
            "jboss_cxf_ver": ["redhat-630187"],
        }
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "present",
            "version": ["Fuse-6.3.0"],
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": "eap_home_bin/fuse_camel_version/"
                "jboss_cxf_ver/"
                "jboss_fuse_on_eap_activemq_ver",
            },
        }
        assert product == expected

    def test_detect_activemq_fuse_absent(self):
        """Test the detect_jboss_fuse method with activemq version found."""
        source = {
            "server_id": self.server_id,
            "source_name": "source1",
            "source_type": "network",
        }
        facts = {
            "jboss_fuse_on_eap_activemq_ver": [
                {"homedir": "/foo/bin", "version": ["redhat-630187"]}
            ]
        }
        product = detect_jboss_fuse(source, facts)
        expected = {
            "name": "JBoss Fuse",
            "presence": "absent",
            "metadata": {
                "server_id": self.server_id,
                "source_name": "source1",
                "source_type": "network",
                "raw_fact_key": None,
            },
        }
        assert product == expected

    def test_get_version(self):
        """Test the get_version method."""
        eap_camel = [{"homedir": "/foo/bin", "version": ["redhat-620133"]}]
        versions = get_version(eap_camel)
        expected = ["redhat-620133"]
        assert versions == expected
