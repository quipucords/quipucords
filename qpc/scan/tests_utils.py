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
"""Test the CLI module."""

import unittest

from qpc.scan import (JBOSS_BRMS,
                      JBOSS_EAP,
                      JBOSS_FUSE,
                      JBOSS_WS)
from qpc.scan.utils import (get_enabled_products,
                            get_optional_products)


class ScanUtilsTests(unittest.TestCase):
    """Class for testing the scan utils."""

    def test_default_optional_values(self):
        """Testing the scan default optional product values."""
        disabled_default = {JBOSS_FUSE: False,
                            JBOSS_EAP: False,
                            JBOSS_BRMS: False,
                            JBOSS_WS: False}
        result = get_optional_products([])
        self.assertEqual(disabled_default, result)

    def test_default_extended_search_values(self):
        """Testing the scan default extended searchvalues."""
        disabled_default = {JBOSS_FUSE: False,
                            JBOSS_EAP: False,
                            JBOSS_BRMS: False,
                            JBOSS_WS: False,
                            'search_directories': []}
        result = get_enabled_products([], [], True)
        self.assertEqual(disabled_default, result)
