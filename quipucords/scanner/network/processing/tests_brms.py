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
from scanner.network.processing.test_util import (ansible_results,
                                                  ansible_result)


class TestProcessJbossBRMSManifestMF(unittest.TestCase):
    """Test ProcessJbossBRMSManifestMF."""

    good_result = {'item': '/tmp/good/',
                   'stdout': 'This is manifest file output',
                   'rc': 0}
    manifest_results = ansible_results([good_result])

    def test_success_case(self):
        """Return a dict of directory: manifest pairs."""
        self.assertEqual(
            brms.ProcessJbossBRMSManifestMF.process(self.manifest_results),
            {self.good_result['item']: self.good_result['stdout']})


class TestProcessJbossBRMSKieBusinessCentral(unittest.TestCase):
    """Test ProcessJbossBRMSKieBusinessCentral."""

    good_result = {'item': '/tmp/good/',
                   'stdout': '/tmp/good/file.file',
                   'rc': 0}
    bad_result = {'item': '/tmp/bad/',
                  'stdout': '',
                  'rc': 1}
    ls_results = ansible_results([good_result, bad_result])

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            brms.ProcessJbossBRMSKieBusinessCentral.process(self.ls_results),
            [self.good_result['stdout']])


class TestProcessFindBRMSKieApiVer(unittest.TestCase):
    """Test ProcessFindBRMSKieApiVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            brms.ProcessFindBRMSKieApiVer.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])


class TestProcessFindBRMSDroolsCoreVer(unittest.TestCase):
    """Test ProcessFindBRMSDroolsCoreVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            brms.ProcessFindBRMSDroolsCoreVer.process(
                ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])


class TestProcessFindBRMSKieWarVer(unittest.TestCase):
    """Test ProcessFindBRMSKieWarVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            brms.ProcessFindBRMSKieWarVer.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])
