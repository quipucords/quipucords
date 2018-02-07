#
# Copyright (c) 2017-2018 Red Hat, Inc.
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
from unittest.mock import patch, ANY
import sys
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from qpc.tests_utilities import HushUpStderr, redirect_stdout, DEFAULT_CONFIG
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.cred import CREDENTIAL_URI
from qpc.cred.list import CredListCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class CredentialListCliTests(unittest.TestCase):
    """Class for testing the credential list commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_list_cred_ssl_err(self):
        """Testing the list credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            alc = CredListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    alc.main(args)
                    self.assertEqual(cred_out.getvalue(), SSL_ERROR_MSG)

    def test_list_cred_conn_err(self):
        """Testing the list credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            alc = CredListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    alc.main(args)
                    self.assertEqual(cred_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_list_cred_internal_err(self):
        """Testing the list credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            alc = CredListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    alc.main(args)
                    self.assertEqual(cred_out.getvalue(), 'Server Error')

    def test_list_cred_empty(self):
        """Testing the list credential command successfully with empty data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            alc = CredListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(cred_out):
                alc.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 'No credentials exist yet.\n')

    @patch('builtins.input', return_value='yes')
    def test_list_cred_data(self, b_input):
        """Testing the list credential command with stubbed data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        credential_entry = {'id': 1, 'name': 'cred1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        next_link = 'http://127.0.0.1:8000/api/v1/credentials/?page=2'
        data = {
            'count': 1,
            'next': 'http://127.0.0.1:8000/api/v1/credentials/?page=2',
            'results': results
        }
        data2 = {
            'count': 1,
            'next': None,
            'results': results
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(next_link, status_code=200, json=data2)
            alc = CredListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(cred_out):
                alc.main(args)
                expected = '[{"id":1,"name":"cred1","password":"********",' \
                    '"username":"root"}]'
                self.assertEqual(cred_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(),
                                 expected + expected)
                b_input.assert_called_with(ANY)

    def test_list_filtered_cred_data(self):
        """Testing the list credential with filter by cred type."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        credential_entry = {'id': 1, 'name': 'cred1', 'cred_type': 'network',
                            'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {
            'count': 1,
            'next': None,
            'results': results
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            alc = CredListCommand(SUBPARSER)
            args = Namespace(type='network')
            with redirect_stdout(cred_out):
                alc.main(args)
                expected = '[{"cred_type":"network","id":1,'\
                    '"name":"cred1","password":"********",' \
                    '"username":"root"}]'
                self.assertEqual(cred_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
