"""Test the product utils."""

from django.test import TestCase

from fingerprinter.utils import strip_prefix, strip_suffix


class ProductUtilsTest(TestCase):
    """Tests Product Utils class."""

    def test_strip_prefix(self):
        """Test the strip_prefix method."""
        string = "/opt/eap/modules.jar"
        prefix = "/opt/eap/"
        stripped = strip_prefix(string, prefix)
        assert stripped == "modules.jar"

    def test_strip_prefix_no_prefix(self):
        """Test the strip_prefix method."""
        string = "/opt/eap/modules.jar"
        prefix = "/opt/fuse/"
        stripped = strip_prefix(string, prefix)
        assert stripped == string

    def test_strip_suffix_no_suffix(self):
        """Test the strip_suffix method."""
        string = "modules.jar"
        suffix = ".csv"
        stripped = strip_suffix(string, suffix)
        assert stripped == string

    def test_strip_suffix(self):
        """Test the strip_suffix method."""
        string = "modules.jar"
        suffix = ".jar"
        stripped = strip_suffix(string, suffix)
        assert stripped == "modules"
