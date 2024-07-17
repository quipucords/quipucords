"""Unit tests for initial processing of date facts."""

import unittest

from scanner.network.processing import date, process
from tests.scanner.network.processing.util_for_test import ansible_result


class ProcessDateFilesystemCreate(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date file system create."""
        self.assertEqual(
            date.ProcessDateFilesystemCreate.process(ansible_result("a\nb\nc")), "c"
        )

    def test_not_found(self):
        """Did not find date file system create."""
        self.assertEqual(
            date.ProcessDateFilesystemCreate.process(ansible_result("")),
            process.NO_DATA,
        )


class ProcessDateMachineId(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date machine id."""
        self.assertEqual(
            date.ProcessDateMachineId.process(ansible_result("a\nb\nc")), "c"
        )

    def test_not_found(self):
        """Did not find date file system create."""
        self.assertEqual(
            date.ProcessDateMachineId.process(ansible_result("")), process.NO_DATA
        )
