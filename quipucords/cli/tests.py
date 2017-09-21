#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the CLI module"""

import unittest
import sys
import six
from cli.cli import CLI
from cli.tests_utilities import HushUpStderr, redirect_stdout


class CliTests(unittest.TestCase):
    """Class for testing the base cli arguments for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_version(self):
        """Testing the verion argument"""
        version_out = six.StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(version_out):
                sys.argv = ['/bin/qpc', '--version']
                CLI().main()
                self.assertEqual(version_out.getvalue(), '0.0.1')
