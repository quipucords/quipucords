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

import os
import sys
import unittest
from unittest.mock import patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO

from qpc import messages
from qpc.cli import CLI
from qpc.cred import (CREDENTIAL_URI,
                      NETWORK_CRED_TYPE,
                      SATELLITE_CRED_TYPE,
                      VCENTER_CRED_TYPE)
from qpc.cred.add import CredAddCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock


TMP_KEY = '/tmp/testkey'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class CredentialAddCliTests(unittest.TestCase):
    """Class for testing the credential add commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
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

    def test_add_req_args_err(self):
        """Testing the add credential command required flags."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'credential',
                        'add', '--name', 'credential1']
            CLI().main()

    def test_add_no_type(self):
        """Testing the add credential without type flag."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'credential',
                        'add', '--name', 'credential1',
                        '--username', 'foo', '--password']
            CLI().main()

    def test_add_bad_key(self):
        """Testing the add credential command.

        When providing an invalid path for the sshkeyfile.
        """
        cred_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(cred_out):
                sys.argv = ['/bin/qpc', 'credential', 'add',
                            '--name', 'credential1',
                            '--username', 'root', '--sshkeyfile', 'bad_path']
                CLI().main()

    def test_add_cred_name_dup(self):
        """Testing the add credential command duplicate name."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        error = {'name': ['credential with this name already exists.']}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=400, json=error)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='cred_dup', username='root',
                             type=NETWORK_CRED_TYPE,
                             filename=TMP_KEY,
                             password=None, become_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    cac.main(args)
                    cac.main(args)

    def test_add_cred_ssl_err(self):
        """Testing the add credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.SSLError)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             type=NETWORK_CRED_TYPE,
                             filename=TMP_KEY,
                             password=None, become_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    cac.main(args)

    def test_add_cred_conn_err(self):
        """Testing the add credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.ConnectTimeout)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             type=NETWORK_CRED_TYPE,
                             filename=TMP_KEY,
                             password=None, become_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    cac.main(args)

    def test_add_host_cred(self):
        """Testing the add host cred command successfully."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             type=NETWORK_CRED_TYPE,
                             filename=TMP_KEY,
                             password=None, ssh_passphrase=None,
                             become_method=None, become_user=None,
                             become_password=None)
            with redirect_stdout(cred_out):
                cac.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 'Credential "credential1" was added.\n')

    def test_add_host_cred_with_become(self):
        """Testing the add host cred command successfully."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             type=NETWORK_CRED_TYPE,
                             filename=TMP_KEY,
                             password=None, ssh_passphrase=None,
                             become_method='sudo', become_user='root',
                             become_password=None)
            with redirect_stdout(cred_out):
                cac.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_ADDED % 'credential1' + '\n')

    @patch('getpass._raw_input')
    def test_add_vcenter_cred(self, do_mock_raw_input):
        """Testing the add vcenter cred command successfully."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1',
                             type=VCENTER_CRED_TYPE,
                             username='root',
                             password='sdf')
            do_mock_raw_input.return_value = 'abc'
            with redirect_stdout(cred_out):
                cac.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CONN_PASSWORD + '\n' +
                                 messages.CRED_ADDED % 'credential1' + '\n')

    @patch('getpass._raw_input')
    def test_add_sat_cred(self, do_mock_raw_input):
        """Testing the add sat cred command successfully."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1',
                             type=SATELLITE_CRED_TYPE,
                             username='root',
                             password='sdf')
            do_mock_raw_input.return_value = 'abc'
            with redirect_stdout(cred_out):
                cac.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CONN_PASSWORD + '\n' +
                                 messages.CRED_ADDED % 'credential1' + '\n')

    @patch('getpass._raw_input')
    def test_add_cred_401(self, do_mock_raw_input):
        """Testing the 401 error flow."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=401)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1',
                             type=SATELLITE_CRED_TYPE,
                             username='root',
                             password='sdf')
            do_mock_raw_input.return_value = 'abc'
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    cac.main(args)

    @patch('getpass._raw_input')
    def test_add_cred_expired(self, do_mock_raw_input):
        """Testing the token expired flow."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            expired = {'detail': 'Token has expired'}
            mocker.post(url, status_code=400, json=expired)
            cac = CredAddCommand(SUBPARSER)
            args = Namespace(name='credential1',
                             type=SATELLITE_CRED_TYPE,
                             username='root',
                             password='sdf')
            do_mock_raw_input.return_value = 'abc'
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    cac.main(args)
