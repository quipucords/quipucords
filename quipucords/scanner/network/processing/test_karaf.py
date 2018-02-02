# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing."""

# pylint: disable=missing-docstring

import unittest
from scanner.network.processing import process, karaf
from scanner.network.processing.test_util import ansible_result, \
    ansible_results


class TestProcessKarafRunningProcesses(unittest.TestCase):
    """Test ProcessKarafRunningPaths."""

    def test_success_case(self):
        """Strip spaces from good input."""
        self.assertEqual(
            karaf.ProcessKarafRunningProcesses.process(
                ansible_result(' good ')),
            'good')

    def test_find_warning(self):
        """Fail if we get the special find warning string."""
        self.assertEqual(
            karaf.ProcessKarafRunningProcesses.process(
                ansible_result(karaf.FIND_WARNING)),
            process.NO_DATA)


class TestProcessFindKaraf(unittest.TestCase):
    """Test ProcessFindJKaraf."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            karaf.ProcessFindKaraf.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])


class TestProcessLocateKaraf(unittest.TestCase):
    """Test using locate to find karaf.jar."""

    def test_success(self):
        """Found karaf.jar."""
        self.assertEqual(
            karaf.ProcessLocateKaraf.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find karaf.jar."""
        self.assertEqual(
            karaf.ProcessLocateKaraf.process(ansible_result('')),
            [])


class TestProcessKarafInitFiles(unittest.TestCase):
    """Test looking for 'jboss' or 'fuse' init files."""

    processors = [karaf.ProcessJbossFuseChkconfig,
                  karaf.ProcessJbossFuseSystemctl]

    def test_no_jboss(self):
        """No 'jboss' or 'fuse' found."""
        for processor in self.processors:
            self.assertEqual(
                # Blank line in input to check that processor will skip it.
                processor.process(ansible_result('foo\nbar\n\nbaz')),
                [])

    def test_jboss(self):
        """'jboss' found."""
        # This tests that the processor returns the 'jboss bar' line
        # and that it does *not* return the 'baz jboss' line, becuase
        # in that line 'jboss' is not in the first piece.
        for processor in self.processors:
            self.assertEqual(
                processor.process(
                    ansible_result('  foo\n  jboss bar\n  baz jboss')),
                ['jboss bar'])

    def test_eap(self):
        """'fuse' found."""
        for processor in self.processors:
            self.assertEqual(
                processor.process(
                    ansible_result('  foo\n  fuse bar\n  baz fuse')),
                ['fuse bar'])


class TestProcessKarafHomeBinFuse(unittest.TestCase):
    """Test using locate to find karaf home bin fuse."""

    def test_success(self):
        """Found karaf.jar."""
        self.assertEqual(
            karaf.ProcessKarafHomeBinFuse.process(ansible_results(
                [{'item': 'foo', 'stdout': 'bin/fuse'}])),
            {'foo': True})

    def test_not_found(self):
        """Did not find karaf home bin fuse."""
        self.assertEqual(
            karaf.ProcessKarafHomeBinFuse.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            {'foo': False})
