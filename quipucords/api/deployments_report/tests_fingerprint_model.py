"""Test the fingerprint model."""
from django.test import TestCase

from api.common.common_report import create_report_version
from api.models import DeploymentsReport
from api.serializers import SystemFingerprintSerializer


class FingerprintModelTest(TestCase):
    """Tests against the Fingerprint model."""

    def setUp(self):
        """Create test case setup."""
        self.deployment_report = DeploymentsReport(
            report_version=create_report_version()
        )
        self.deployment_report.save()

    ################################################################
    # Test Model Create
    ################################################################
    def test_empty_fingerprint(self):
        """Create an empty fingerprint."""
        fingerprint_dict = {
            "deployment_report": self.deployment_report.id,
            "metadata": {},
            "sources": [],
        }

        serializer = SystemFingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    # pylint: disable=invalid-name
    def test_product_with_version_fingerprint(self):
        """Create a fingerprint with products."""
        product_dict = {
            "name": "product1",
            "presence": "unknown",
            "version": ["1", "2"],
            "metadata": {},
        }
        fingerprint_dict = {
            "deployment_report": self.deployment_report.id,
            "metadata": {},
            "products": [product_dict],
            "sources": [],
        }

        serializer = SystemFingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    def test_product_fingerprint(self):
        """Create a fingerprint with products."""
        product_dict = {"name": "product1", "presence": "unknown", "metadata": {}}
        fingerprint_dict = {
            "deployment_report": self.deployment_report.id,
            "metadata": {},
            "products": [product_dict],
            "sources": [],
        }

        serializer = SystemFingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    def test_entitlement_fingerprint(self):
        """Create a fingerprint with entitlements."""
        entitlement_dict = {
            "name": "RHEL Server",
            "entitlement_id": "69",
            "metadata": {},
        }
        fingerprint_dict = {
            "deployment_report": self.deployment_report.id,
            "metadata": {},
            "entitlements": [entitlement_dict],
            "sources": [],
        }

        serializer = SystemFingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()
