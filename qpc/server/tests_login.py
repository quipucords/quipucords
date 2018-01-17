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
from unittest.mock import patch
import sys
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests_mock
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config
from qpc.server import LOGIN_URI
from qpc.server.login_host import LoginHostCommand


TMP_KEY = '/tmp/testkey'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class LoginCliTests(unittest.TestCase):
    """Class for testing the login server command for qpc."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    @patch('getpass._raw_input')
    def test_login_bad_cred(self, do_mock_raw_input):
        """Testing the login with bad creds."""
        server_out = StringIO()
        url = BASE_URL + LOGIN_URI
        e_msg = 'Unable to log in with provided credentials.'
        error = {'detail': [e_msg]}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=400, json=error)
            lhc = LoginHostCommand(SUBPARSER)
            lhc.password = 'password'
            args = Namespace(username='admin')
            do_mock_raw_input.return_value = 'abc'
            with self.assertRaises(SystemExit):
                with redirect_stdout(server_out):
                    lhc.main(args)
                    self.assertTrue(e_msg in server_out.getvalue())

    @patch('getpass._raw_input')
    def test_login_good(self, do_mock_raw_input):
        """Testing the login with good creds."""
        server_out = StringIO()
        url = BASE_URL + LOGIN_URI
        error = {'token': 'a_token'}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200, json=error)
            lhc = LoginHostCommand(SUBPARSER)
            lhc.password = 'password'
            args = Namespace(username='admin')
            do_mock_raw_input.return_value = 'abc'
            with redirect_stdout(server_out):
                lhc.main(args)
                self.assertEqual(server_out.getvalue(), 'Login successful.\n')
