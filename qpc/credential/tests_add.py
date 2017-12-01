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
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.credential import CREDENTIAL_URI
from qpc.credential.add import CredentialAddCommand
from qpc.utils import get_server_location, write_server_config

TMP_KEY = '/tmp/testkey'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class CredentialAddCliTests(unittest.TestCase):
    """Class for testing the credential add commands for qpc."""

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

    def test_add_req_args_err(self):
        """Testing the add credential command required flags."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'credential', 'add', '--name', 'credential1']
            CLI().main()

    def test_add_bad_key(self):
        """Testing the add credential command.

        When providing an invalid path for the sshkeyfile.
        """
        cred_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(cred_out):
                sys.argv = ['/bin/qpc', 'credential', 'add', '--name', 'credential1',
                            '--username', 'root', '--sshkeyfile', 'bad_path']
                CLI().main()

    def test_add_cred_name_dup(self):
        """Testing the add credential command duplicate name."""
        cred_out = StringIO()
        url = BASE_URL + CREDENTIAL_URI
        error = {'name': ['credential with this name already exists.']}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=400, json=error)
            aac = CredentialAddCommand(SUBPARSER)
            args = Namespace(name='cred_dup', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aac.main(args)
                    aac.main(args)
                    self.assertTrue('credential with this name already exists.'
                                    in cred_out.getvalue())

    def test_add_cred_ssl_err(self):
        """Testing the add credential command with a connection error."""
        cred_out = StringIO()
        url = BASE_URL + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.SSLError)
            aac = CredentialAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aac.main(args)
                    self.assertEqual(cred_out.getvalue(), SSL_ERROR_MSG)

    def test_add_cred_conn_err(self):
        """Testing the add credential command with a connection error."""
        cred_out = StringIO()
        url = BASE_URL + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.ConnectTimeout)
            aac = CredentialAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             filename=TMP_KEY,
                             password=None, sudo_password=None,
                             ssh_passphrase=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aac.main(args)
                    self.assertEqual(cred_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_add_cred(self):
        """Testing the add credential command successfully."""
        cred_out = StringIO()
        url = BASE_URL + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            aac = CredentialAddCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root', filename=TMP_KEY,
                             password=None, sudo_password=None,
                             ssh_passphrase=None)
            with redirect_stdout(cred_out):
                aac.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 'Credential "credential1" was added\n')
