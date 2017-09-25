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
import os
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from cli.cli import CLI
from cli.tests_utilities import HushUpStderr, redirect_stdout
from cli.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from cli.auth import AUTH_URI_POST
from cli.auth.add import AuthAddCommand

TMP_KEY = "/tmp/testkey"
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class AuthCliTests(unittest.TestCase):
    """Class for testing the auth cli commands for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        if os.path.isfile(TMP_KEY):
            os.remove(TMP_KEY)
        with open(TMP_KEY, 'w') as test_sshkey:
            test_sshkey.write('fake ssh keyfile.')

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr
        if os.path.isfile(TMP_KEY):
            os.remove(TMP_KEY)

    def test_add_req_args_err(self):
        """Testing the add auth command required flags"""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'auth', 'add', '--name', 'auth1']
            CLI().main()

    def test_add_bad_key(self):
        """Testing the add auth command when providing an invalid path for
        the sshkeyfile.
        """
        auth_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(auth_out):
                sys.argv = ['/bin/qpc', 'auth', 'add', '--name', 'auth1',
                            '--username', 'root', '--sshkeyfile', 'bad_path']
                CLI().main()

    def test_add_auth_name_dup(self):
        """Testing the add auth command duplicate name
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI_POST
        error = {'name': ['credential with this name already exists.']}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=400, json=error)
            aac = AuthAddCommand(SUBPARSER)
            args = Namespace(name='auth_dup', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aac.main(args)
                    aac.main(args)
                    self.assertTrue('credential with this name already exists.'
                                    in auth_out.getvalue())

    def test_add_auth_ssl_err(self):
        """Testing the add auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI_POST
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.SSLError)
            aac = AuthAddCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aac.main(args)
                    self.assertEqual(auth_out.getvalue(), SSL_ERROR_MSG)

    def test_add_auth_conn_err(self):
        """Testing the add auth command with a connection error
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI_POST
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.ConnectTimeout)
            aac = AuthAddCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(auth_out):
                    aac.main(args)
                    self.assertEqual(auth_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_add_auth(self):
        """Testing the add auth command successfully
        """
        auth_out = StringIO()
        url = BASE_URL + AUTH_URI_POST
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            aac = AuthAddCommand(SUBPARSER)
            args = Namespace(name='auth1', username='root', filename=TMP_KEY,
                             password=None, sudo_password=None)
            with redirect_stdout(auth_out):
                aac.main(args)
                self.assertEqual(auth_out.getvalue(),
                                 'Auth "auth1" was added\n')
