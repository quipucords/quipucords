"""Unit tests for initial processing of date facts."""


import unittest

from scanner.network.processing import date, process
from scanner.network.processing.util_for_test import ansible_result


class TestProcessDateDate(unittest.TestCase):
    """Test ProcessDateDate."""

    def test_success_case(self):
        """Found date."""
        assert date.ProcessDateDate.process(ansible_result("a\nb\nc")) == "a"

    def test_not_found(self):
        """Did not find date."""
        assert date.ProcessDateDate.process(ansible_result("")) == process.NO_DATA


class ProcessDateFilesystemCreate(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date file system create."""
        assert (
            date.ProcessDateFilesystemCreate.process(ansible_result("a\nb\nc")) == "a"
        )

    def test_not_found(self):
        """Did not find date file system create."""
        assert (
            date.ProcessDateFilesystemCreate.process(ansible_result(""))
            == process.NO_DATA
        )


class ProcessDateMachineId(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date machine id."""
        assert date.ProcessDateMachineId.process(ansible_result("a\nb\nc")) == "a"

    def test_not_found(self):
        """Did not find date file system create."""
        assert date.ProcessDateMachineId.process(ansible_result("")) == process.NO_DATA


class ProcessDateYumHistory(unittest.TestCase):
    """Test ProcessDateYumHistory."""

    def test_success_case(self):
        """Found date yum history."""
        assert (
            date.ProcessDateYumHistory.process(ansible_result("\n2017-07-25"))
            == "2017-07-25"
        )

    def test_not_found(self):
        """Did not find date yum history."""
        assert date.ProcessDateYumHistory.process(ansible_result("")) == process.NO_DATA
