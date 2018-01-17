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
"""Test the CLI module."""

import unittest
import sys
import os
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr
from qpc.utils import QPC_CLIENT_TOKEN


class LogoutTests(unittest.TestCase):
    """Class for testing the logout host function."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_success_config_server(self):
        """Testing the logout server green path."""
        sys.argv = ['/bin/qpc', 'server', 'logout']
        CLI().main()

        self.assertFalse(os.path.exists(QPC_CLIENT_TOKEN))
