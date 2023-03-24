"""Test the fingerprinter utils."""

from django.test import TestCase

from fingerprinter.utils import product_entitlement_found


class FingerprinterUtilTest(TestCase):
    """Tests Fingerprinter Utils class."""

    def test_product_entitlement_no_name(self):
        """Test product entitlement without name is false."""
        result = product_entitlement_found([{}], "Foo")
        assert not result
