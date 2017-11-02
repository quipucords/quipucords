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
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.auth import AUTH_URI
from qpc.auth.edit import AuthEditCommand

TMP_KEY = '/tmp/testkey'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class AuthEditCliTests(unittest.TestCase):
    """Class for testing the auth edit commands for qpc."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        if os.path.isfile(TMP_KEY):
            os.remove(TMP_KEY)
        with open(TMP_KEY, 'w') as test_sshkey:
            test_sshkey.write('fake ssh keyfile.')

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        if os.path.isfile(TMP_KEY):
            os.remove(TMP_KEY)

    def test_edit_req_args_err(self):
        """Testing the auth edit command required flags."""
        auth_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(auth_out):
                sys.argv = ['/bin/qpc', 'auth', 'edit', '--name', 'auth1']
                CLI().main()
                self.assertEqual(auth_out.getvalue(),
                                 'No arguments provided to edit '
                                 'credential auth1')

    def test_edit_bad_key(self):
        """Testing the auth edit command.

        When providing an invalid path for the sshkeyfile.
        """
        auth_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(auth_out):
                sys.argv = ['/bin/qpc', 'auth', 'edit', '--name', 'auth1',
                            '--sshkeyfile', 'bad_path']
                CLI().main()
                self.assertTrue('Please provide a valid location for the '
                                '"--sshkeyfile" argument.'
                                in auth_out.getvalue())

    def test_edit_auth_none(self):
        """Testing the edit auth command for none existing auth."""
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI + '?name=auth_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            aec = AuthEditCommand(SUBPARSER)
            args = Namespace(name='auth_none', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue('Auth "auth_none" does not exist'
                                    in auth_out.getvalue())

    def test_edit_auth_ssl_err(self):
        """Testing the edit auth command with a connection error."""
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            aec = AuthEditCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aec.main(args)
                    self.assertEqual(auth_out.getvalue(), SSL_ERROR_MSG)

    def test_edit_auth_conn_err(self):
        """Testing the edit auth command with a connection error."""
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            aec = AuthEditCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aec.main(args)
                    self.assertEqual(auth_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_edit_auth(self):
        """Testing the edit auth command successfully."""
        auth_out = StringIO()
        url_get = BASE_URL + AUTH_URI
        url_patch = BASE_URL + AUTH_URI + '1/'
        data = [{'id': 1, 'name': 'auth1', 'username': 'root',
                 'password': '********'}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = AuthEditCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root', filename=TMP_KEY,
                             password=None, sudo_password=None,
                             ssh_passphrase=None)
            with redirect_stdout(auth_out):
                aec.main(args)
                self.assertEqual(auth_out.getvalue(),
                                 'Auth "auth1" was updated\n')

    def test_edit_auth_get_error(self):
        """Testing the edit auth command server error occurs."""
        auth_out = StringIO()
        url_get = BASE_URL + AUTH_URI
        data = [{'id': 1, 'name': 'auth1', 'username': 'root',
                 'password': '********'}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=500, json=data)
            aec = AuthEditCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root', filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aec.main(args)
                    self.assertEqual(auth_out.getvalue(),
                                     'Auth "auth1" does not exist\n')
