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
