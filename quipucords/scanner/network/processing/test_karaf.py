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
from scanner.network.processing.test_util import ansible_result


class TestProcessKarafRunningProcesses(unittest.TestCase):
    """Test ProcessJbossEapRunningPaths."""

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
    """Test ProcessFindJBoss."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            karaf.ProcessFindKaraf.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])


class TestProcessLocateKaraf(unittest.TestCase):
    """Test using locate to find jboss-modules.jar."""

    def test_success(self):
        """Found jboss-modules.jar."""
        self.assertEqual(
            karaf.ProcessLocateKaraf.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find jboss-modules.jar."""
        self.assertEqual(
            karaf.ProcessLocateKaraf.process(ansible_result('')),
            [])
