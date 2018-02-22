# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of cpu facts."""


import unittest
from scanner.network.processing import process
from scanner.network.processing import cpu
from scanner.network.processing.test_util import ansible_result


class TestProcessCpuModelVer(unittest.TestCase):
    """Test ProcessCpuModelVer."""

    def test_success_case(self):
        """Found cpu model ver."""
        self.assertEqual(
            cpu.ProcessCpuModelVer.process(
                ansible_result('a\nb\nc')),
            'a')

    def test_not_found(self):
        """Did not find cpu model ver."""
        self.assertEqual(
            cpu.ProcessCpuModelVer.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuCpuFamily(unittest.TestCase):
    """Test ProcessCpuCpuFamily."""

    def test_success_case(self):
        """Found cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu family."""
        self.assertEqual(
            cpu.ProcessCpuCpuFamily.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuVendorId(unittest.TestCase):
    """Test ProcessCpuVendorId."""

    def test_success_case(self):
        """Found cpu vendor id."""
        self.assertEqual(
            cpu.ProcessCpuVendorId.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu vendor id."""
        self.assertEqual(
            cpu.ProcessCpuVendorId.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuModelName(unittest.TestCase):
    """Test ProcessCpuModelName."""

    def test_success_case(self):
        """Found cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu model name."""
        self.assertEqual(
            cpu.ProcessCpuModelName.process(
                ansible_result('')),
            process.NO_DATA)


class TestProcessCpuBogomips(unittest.TestCase):
    """Test ProcessCpuBogomips."""

    def test_success_case(self):
        """Found cpu bogomips."""
        self.assertEqual(
            cpu.ProcessCpuBogomips.process(
                ansible_result('a\nb\nc')),
            'a')

    def test__not_found(self):
        """Did not find cpu bogomips."""
        self.assertEqual(
            cpu.ProcessCpuBogomips.process(
                ansible_result('')),
            process.NO_DATA)
