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
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.auth import AUTH_URI
from qpc.auth.clear import AuthClearCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class AuthClearCliTests(unittest.TestCase):
    """Class for testing the auth clear commands for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_clear_auth_ssl_err(self):
        """Testing the clear auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    self.assertEqual(auth_out.getvalue(), SSL_ERROR_MSG)

    def test_clear_auth_conn_err(self):
        """Testing the clear auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    self.assertEqual(auth_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_clear_auth_internal_err(self):
        """Testing the clear auth command with an internal error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    self.assertEqual(auth_out.getvalue(), 'Server Error')

    def test_clear_auth_empty(self):
        """Testing the clear auth command successfully with empty data
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    self.assertEqual(auth_out.getvalue(),
                                     'Auth "auth1"  was not found\n')

    def test_clear_by_name(self):
        """Testing the clear auth command successfully with stubbed data
        when specifying a name
        """
        auth_out = StringIO()
        get_url = BASE_URL + AUTH_URI + '?name=auth1'
        delete_url = BASE_URL + AUTH_URI + '1/'
        auth_entry = {'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with redirect_stdout(auth_out):
                acc.main(args)
                expected = 'Auth "auth1" was removed\n'
                self.assertEqual(auth_out.getvalue(), expected)

    def test_clear_by_name_err(self):
        """Testing the clear auth command successfully with stubbed data
        when specifying a name with an error response
        """
        auth_out = StringIO()
        get_url = BASE_URL + AUTH_URI + '?name=auth1'
        delete_url = BASE_URL + AUTH_URI + '1/'
        auth_entry = {'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}
        data = [auth_entry]
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    expected = 'Failed to remove credential "auth1"'
                    self.assertTrue(expected in auth_out.getvalue())

    def test_clear_all_empty(self):
        """Testing the clear auth command successfully with stubbed data
        empty list of credentials
        """
        auth_out = StringIO()
        get_url = BASE_URL + AUTH_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=[])
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    expected = 'No credentials exist to be removed\n'
                    self.assertEqual(auth_out.getvalue(), expected)

    def test_clear_all_with_error(self):
        """Testing the clear auth command successfully with stubbed data
        a list of credentials with delete error
        """
        auth_out = StringIO()
        get_url = BASE_URL + AUTH_URI
        delete_url = BASE_URL + AUTH_URI + '1/'
        auth_entry = {'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}
        data = [auth_entry]
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    acc.main(args)
                    expected = 'Some credentials were removed, however and' \
                               ' error occurred removing the following' \
                               ' credentials:'
                    self.assertTrue(expected in auth_out.getvalue())

    def test_clear_all(self):
        """Testing the clear auth command successfully with stubbed data
        a list of credentials
        """
        auth_out = StringIO()
        get_url = BASE_URL + AUTH_URI
        delete_url = BASE_URL + AUTH_URI + '1/'
        auth_entry = {'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            acc = AuthClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with redirect_stdout(auth_out):
                acc.main(args)
                expected = 'All credentials were removed\n'
                self.assertEqual(auth_out.getvalue(), expected)
