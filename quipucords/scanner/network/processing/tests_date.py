# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of date facts."""


import unittest
from scanner.network.processing import date
from scanner.network.processing.test_util import ansible_result


class TestProcessDateDate(unittest.TestCase):
    """Test ProcessDateDate."""

    def test_success_case(self):
        """Found date."""
        self.assertEqual(
            date.ProcessDateDate.process(
                ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find date."""
        self.assertEqual(
            date.ProcessDateDate.process(
                ansible_result('')),
            [])


class ProcessDateFilesystemCreate(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date file system create."""
        self.assertEqual(
            date.ProcessDateFilesystemCreate.process(
                ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find date file system create."""
        self.assertEqual(
            date.ProcessDateFilesystemCreate.process(
                ansible_result('')),
            [])


class ProcessDateMachineId(unittest.TestCase):
    """Test ProcessDateFilesystemCreate."""

    def test_success_case(self):
        """Found date machine id."""
        self.assertEqual(
            date.ProcessDateMachineId.process(
                ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find date file system create."""
        self.assertEqual(
            date.ProcessDateMachineId.process(
                ansible_result('')),
            [])
