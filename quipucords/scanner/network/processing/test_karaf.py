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

from scanner.network.processing import karaf, process
from scanner.network.processing.util_for_test import ansible_result, \
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
        """No 'fuse' found."""
        for processor in self.processors:
            self.assertEqual(
                # Blank line in input to check that processor will skip it.
                processor.process(ansible_result('foo\nbar\n\nbaz')),
                [])

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


class TestProcessKarafHomeSystemOrgJboss(unittest.TestCase):
    """Test using locate to find karaf home bin fuse."""

    def test_success(self):
        """Found karaf.jar."""
        self.assertEqual(
            karaf.ProcessKarafHomeSystemOrgJboss.process(ansible_results(
                [{'item': 'foo', 'stdout': 'bar'}])),
            {str(['bar']): True})

    def test_not_found(self):
        """Did not find karaf home bin fuse."""
        self.assertEqual(
            karaf.ProcessKarafHomeSystemOrgJboss.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            {'[]': False})


class TestProcessJbossFuseCamelVersion(unittest.TestCase):
    """Test the output of looking for camel version."""

    def test_success(self):
        """Found camel-core."""
        self.assertEqual(
            karaf.ProcessJbossFuseCamelVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def test_not_found(self):
        """Did not find camel-core."""
        self.assertEqual(
            karaf.ProcessJbossFuseCamelVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def on_eap_test_success(self):
        """Found camel on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapCamelVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def on_eap_test_not_found(self):
        """Did not find camel on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapCamelVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def locate_test_success(self):
        """Found camel with locate."""
        self.assertEqual(
            karaf.ProcessLocateCamel.process(ansible_results(
                [{'item': '/fake/dir', 'stdout_lines': 'redhat-630187'}])),
            list(set('redhat-630187')))

    def locate_test_not_found(self):
        """Did not find camel with locate."""
        self.assertEqual(
            karaf.ProcessLocateCamel.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])


class TestProcessJbossFuseActivemqVersion(unittest.TestCase):
    """Test the output of looking for activemq version."""

    def test_success(self):
        """Found activemq."""
        self.assertEqual(
            karaf.ProcessJbossFuseActivemqVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def test_not_found(self):
        """Did not find activemq."""
        self.assertEqual(
            karaf.ProcessJbossFuseActivemqVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def on_eap_test_success(self):
        """Found activemq on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapActivemqVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def on_eap_test_not_found(self):
        """Did not find activemq on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapActivemqVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def locate_test_success(self):
        """Found activemq with locate."""
        self.assertEqual(
            karaf.ProcessLocateActivemq.process(ansible_results(
                [{'item': '/fake/dir', 'stdout_lines': 'redhat-630187'}])),
            list(set('redhat-630187')))

    def locate_test_not_found(self):
        """Did not find activemq with locate."""
        self.assertEqual(
            karaf.ProcessLocateActivemq.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])


class TestProcessJbossFuseCxfVersion(unittest.TestCase):
    """Test the output of looking for cxf version."""

    def test_success(self):
        """Found cxf."""
        self.assertEqual(
            karaf.ProcessJbossFuseCxfVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def test_not_found(self):
        """Did not find cxf."""
        self.assertEqual(
            karaf.ProcessJbossFuseCxfVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def on_eap_test_success(self):
        """Found cxf on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapCxfVersion.process(ansible_results(
                [{'item': '/fake/dir', 'stdout': 'redhat-630187'}])),
            [{'install_home': '/fake/dir',
              'version': ['redhat-630187']}])

    def on_eap_test_not_found(self):
        """Did not find cxf on eap home dir."""
        self.assertEqual(
            karaf.ProcessJbossFuseOnEapCxfVersion.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])

    def locate_test_success(self):
        """Found cxf with locate."""
        self.assertEqual(
            karaf.ProcessLocateCxf.process(ansible_results(
                [{'item': '/fake/dir', 'stdout_lines': 'redhat-630187'}])),
            list(set('redhat-630187')))

    def locate_test_not_found(self):
        """Did not find cxf with locate."""
        self.assertEqual(
            karaf.ProcessLocateCxf.process(ansible_results(
                [{'item': 'foo', 'stdout': '', 'rc': 1}])),
            [])
