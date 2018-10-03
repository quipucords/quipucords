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
import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.cred import CREDENTIAL_URI
from qpc.cred.clear import CredClearCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock


PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class CredentialClearCliTests(unittest.TestCase):
    """Class for testing the credential clear commands for qpc."""

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

    def test_clear_cred_ssl_err(self):
        """Testing the clear credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_cred_conn_err(self):
        """Testing the clear credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_cred_internal_err(self):
        """Testing the clear credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_cred_empty(self):
        """Testing the clear credential command with empty data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=cred1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='cred1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_by_name(self):
        """Testing the clear credential command with stubbed data."""
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        delete_url = get_server_location() + CREDENTIAL_URI + '1/'
        credential_entry = {'id': 1, 'name': 'credential1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with redirect_stdout(cred_out):
                ccc.main(args)
                expected = messages.CRED_REMOVED % 'credential1' + '\n'
                self.assertEqual(cred_out.getvalue(), expected)

    def test_clear_by_name_err(self):
        """Testing the clear credential command successfully with stubbed data.

        When specifying a name with an error response
        """
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        delete_url = get_server_location() + CREDENTIAL_URI + '1/'
        credential_entry = {'id': 1, 'name': 'credential1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {'count': 1, 'results': results}
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_all_empty(self):
        """Testing the clear credential command successfully with stubbed data.

        With empty list of credentials.
        """
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={'count': 0})
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    ccc.main(args)

    def test_clear_all_with_error(self):
        """Testing the clear credential command successfully with stubbed data.

        With a list of credentials with delete error.
        """
        get_url = get_server_location() + CREDENTIAL_URI
        delete_url = get_server_location() + CREDENTIAL_URI + '1/'
        credential_entry = {'id': 1, 'name': 'credential1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {'count': 1, 'results': results}
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                ccc.main(args)

    def test_clear_all(self):
        """Testing the clear credential command successfully with stubbed data.

        With a list of credentials.
        """
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI
        delete_url = get_server_location() + CREDENTIAL_URI + '1/'
        credential_entry = {'id': 1, 'name': 'credential1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            ccc = CredClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with redirect_stdout(cred_out):
                ccc.main(args)
                expected = messages.CRED_CLEAR_ALL_SUCCESS + '\n'
                self.assertEqual(cred_out.getvalue(), expected)
