#
# Copyright (c) 2020 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Test the fingerprinter utils."""

from django.test import TestCase

from fingerprinter.utils import product_entitlement_found


class FingerprinterUtilTest(TestCase):
    """Tests Fingerprinter Utils class."""

    def test_product_entitlement_no_name(self):
        """Test product entitlement without name is false."""
        result = product_entitlement_found([{}], "Foo")
        self.assertFalse(result)
