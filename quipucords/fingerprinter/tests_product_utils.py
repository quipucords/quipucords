#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

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
        self.assertEqual(stripped, "modules.jar")

    def test_strip_prefix_no_prefix(self):
        """Test the strip_prefix method."""
        string = "/opt/eap/modules.jar"
        prefix = "/opt/fuse/"
        stripped = strip_prefix(string, prefix)
        self.assertEqual(stripped, string)

    def test_strip_suffix_no_suffix(self):
        """Test the strip_suffix method."""
        string = "modules.jar"
        suffix = ".csv"
        stripped = strip_suffix(string, suffix)
        self.assertEqual(stripped, string)

    def test_strip_suffix(self):
        """Test the strip_suffix method."""
        string = "modules.jar"
        suffix = ".jar"
        stripped = strip_suffix(string, suffix)
        self.assertEqual(stripped, "modules")
