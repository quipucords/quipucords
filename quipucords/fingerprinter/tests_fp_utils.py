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

"""Test the fact engine utils."""

from django.test import TestCase
from fingerprinter.utils import product_entitlement_found


class EngineTest(TestCase):
    """Tests Utils class."""

    def test_process_network_source(self):
        """Test process network source."""
        result = product_entitlement_found([{}], 'Foo')
        self.assertFalse(result)
