# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of subman facts."""


import unittest

from scanner.network.processing import subman
from scanner.network.processing.util_for_test import ansible_result


class TestProcessSubmanConsumed(unittest.TestCase):
    """Test ProcessSubmanConsumed."""

    def test_success_case(self):
        """Found subman_consumed."""
        self.assertEqual(
            subman.ProcessSubmanConsumed.process(
                ansible_result("subnameA - 1\nsubnameB - 2\nsubnameC - 3")
            ),
            [
                {"name": "subnameA", "entitlement_id": "1"},
                {"name": "subnameB", "entitlement_id": "2"},
                {"name": "subnameC", "entitlement_id": "3"},
            ],
        )

    def test_not_found(self):
        """Did not find subman_consumed."""
        self.assertEqual(subman.ProcessSubmanConsumed.process(ansible_result("")), [])

    def test_empty_string(self):
        """Found empty string."""
        self.assertEqual(
            subman.ProcessSubmanConsumed.process(ansible_result("\n\r")), []
        )
