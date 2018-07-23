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

from scanner.network.processing import jws
from scanner.network.processing.util_for_test import (ansible_result,
                                                      ansible_results)


class TestProcessJWSInstalledWithRpm(unittest.TestCase):
    """Test ProcessJWSInstalledWithRpm."""

    def test_installed_with_rpm(self):
        """Return true if jws was installed with rpm."""
        self.assertEqual(jws.ProcessJWSInstalledWithRpm.
                         process(ansible_result('Red Hat JBoss Web Server')),
                         True)

    def test_not_installed_with_rpm(self):
        """Return false if jws was not installed with rpm."""
        self.assertEqual(jws.ProcessJWSInstalledWithRpm.
                         process(ansible_result('Not installed')), False)


class TestProcessHasJBossEula(unittest.TestCase):
    """Test ProcessHasJBossEULA."""

    def test_has_eula_file(self):
        """Return true if jboss eula file exists."""
        self.assertEqual(jws.ProcessHasJBossEULA.
                         process(ansible_result('JBossEula.txt')), True)

    def test_has_no_eula_file(self):
        """Return false if jboss eula file does not exist."""
        ls_err = 'No such file or directory'
        self.assertEqual(jws.ProcessHasJBossEULA.
                         process(ansible_result(ls_err)), False)


class TestProcessGetVersion(unittest.TestCase):
    """Test ProcessGetVersion."""

    def test_parse_versions(self):
        """Return stdout_lines of ansible result as an array."""
        self.assertEqual(jws.ProcessGetVersion.
                         process(ansible_results(
                             [{'stdout': 'some version string'}])),
                         ['some version string'])


class TestProcessTomcatPartOfRedhatProduct(unittest.TestCase):
    """Test ProcessTomcatPartOfRedhatProduct."""

    def test_true(self):
        """Return True if tomcat was installed as part of a redhat product."""
        self.assertEqual(jws.ProcessTomcatPartOfRedhatProduct.
                         process(ansible_result('True')), True)

    def test_false(self):
        """Return False if tomcat is not part of a redhat product."""
        self.assertEqual(jws.ProcessTomcatPartOfRedhatProduct.
                         process(ansible_result('False')), False)
