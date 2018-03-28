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
from scanner.network.processing import brms
from scanner.network.processing.util_for_test import (ansible_results,
                                                      ansible_result,
                                                      ansible_item)


class TestProcessJbossBRMSManifestMF(unittest.TestCase):
    """Test ProcessJbossBRMSManifestMF."""

    # This is a portion of the BRMS 6.4.0 MANIFEST.MF
    MANIFEST = """Manifest-Version: 1.0
Implementation-Title: KIE Drools Workbench - Distribution Wars
Implementation-Version: 6.5.0.Final-redhat-2
"""

    def test_success(self):
        """Extract the Implementation_Version from a manifest."""
        self.assertEqual(
            brms.ProcessJbossBRMSManifestMF.process_item(
                ansible_item('/opt/brms/', self.MANIFEST)),
            ('/opt/brms', '6.5.0.Final-redhat-2'))

    def test_no_version(self):
        """Don't crash if the manifest is missing a version."""
        self.assertIsNone(
            brms.ProcessJbossBRMSManifestMF.process_item(
                ansible_item('manifest', 'not\na\nmanifest')))


class TestEnclosingWarArchive(unittest.TestCase):
    """Test enclosing_war_archive."""

    def test_enclosing(self):
        """Return the enclosing war archive."""
        self.assertEqual(
            brms.enclosing_war_archive('/foo/kie-server.war/bar/baz'),
            '/foo/kie-server.war')

    def test_war_root(self):
        """Return the war archive when applied to just the archive."""
        self.assertEqual(
            brms.enclosing_war_archive('/foo/kie-server.war'),
            '/foo/kie-server.war')

    def test_no_war_archive(self):
        """Return None when there is no war archive."""
        self.assertIsNone(
            brms.enclosing_war_archive('/foo/bar/baz'))


class TestProcessJbossBRMSKieBusinessCentral(unittest.TestCase):
    """Test ProcessJbossBRMSKieBusinessCentral."""

    good_result = {'item': '/tmp/good/',
                   'stdout': '/tmp/good/kie-api-version-string.jar-1234',
                   'rc': 0}
    bad_result = {'item': '/tmp/bad/',
                  'stdout': '',
                  'rc': 1}
    ls_results = ansible_results([good_result, bad_result])

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            set(
                brms.ProcessJbossBRMSKieBusinessCentral.process(
                    self.ls_results)),
            {('/tmp/good', 'version-string')})


class TestJarNameProcessor(unittest.TestCase):
    """Test JarNameProcessor."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            set(brms.JarNameProcessor.process(
                ansible_result('/a\n/b\n/foo/c'))),
            {('/', 'a'), ('/', 'b'), ('/foo', 'c')})


class TestProcessFindBRMSKieWarVer(unittest.TestCase):
    """Test ProcessFindBRMSKieWarVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            brms.ProcessFindBRMSKieWarVer.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])
