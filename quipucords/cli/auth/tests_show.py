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
from cli.tests_utilities import HushUpStderr, redirect_stdout
from cli.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from cli.auth import AUTH_URI
from cli.auth.show import AuthShowCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class AuthShowCliTests(unittest.TestCase):
    """Class for testing the auth show commands for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_show_auth_ssl_err(self):
        """Testing the list auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            asc = AuthShowCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    asc.main(args)
                    self.assertEqual(auth_out.getvalue(), SSL_ERROR_MSG)

    def test_show_auth_conn_err(self):
        """Testing the list auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            asc = AuthShowCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    asc.main(args)
                    self.assertEqual(auth_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_show_auth_internal_err(self):
        """Testing the list auth command with an internal error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            asc = AuthShowCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    asc.main(args)
                    self.assertEqual(auth_out.getvalue(), 'Server Error')

    def test_show_auth_empty(self):
        """Testing the list auth command successfully with empty data
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            asc = AuthShowCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    asc.main(args)
                    self.assertEqual(auth_out.getvalue(),
                                     'Auth "auth1" does not exist\n')

    def test_show_auth_data(self):
        """Testing the list auth command successfully with stubbed data
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth1'
        auth_entry = {'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            asc = AuthShowCommand(SUBPARSER)
            args = Namespace(name='auth1')
            with redirect_stdout(auth_out):
                asc.main(args)
                expected = '{"id":1,"name":"auth1","password":"********",' \
                    '"username":"root"}'
                self.assertEqual(auth_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
