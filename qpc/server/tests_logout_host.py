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

import os
import sys
import unittest
from argparse import ArgumentParser, Namespace

from qpc.server import LOGOUT_URI
from qpc.server.logout_host import LogoutHostCommand
from qpc.tests_utilities import HushUpStderr
from qpc.utils import QPC_CLIENT_TOKEN, get_server_location

import requests_mock


PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


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

    def test_success_logout(self):
        """Testing the logout server green path."""
        url = get_server_location() + LOGOUT_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200)
            lhc = LogoutHostCommand(SUBPARSER)
            args = Namespace()
            lhc.main(args)
            self.assertFalse(os.path.exists(QPC_CLIENT_TOKEN))
