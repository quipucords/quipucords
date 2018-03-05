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
import sys
import os
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
import qpc.messages as messages
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout, DEFAULT_CONFIG
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.cred import (CREDENTIAL_URI,
                      NETWORK_CRED_TYPE,
                      VCENTER_CRED_TYPE,
                      SATELLITE_CRED_TYPE)
from qpc.cred.edit import CredEditCommand
from qpc.utils import get_server_location, write_server_config

TMP_KEY = '/tmp/testkey'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class CredentialEditCliTests(unittest.TestCase):
    """Class for testing the credential edit commands for qpc."""

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

    def test_edit_req_args_err(self):
        """Testing the credential edit command required flags."""
        cred_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(cred_out):
                sys.argv = ['/bin/qpc', 'credential',
                            'edit', '--name', 'credential1']
                CLI().main()
                self.assertEqual(cred_out.getvalue(),
                                 'No arguments provided to edit '
                                 'credential credential1')

    def test_edit_bad_key(self):
        """Testing the credential edit command.

        When providing an invalid path for the sshkeyfile.
        """
        cred_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(cred_out):
                sys.argv = ['/bin/qpc', 'credential', 'edit',
                            '--name', 'cred1',
                            '--sshkeyfile', 'bad_path']
                CLI().main()
                self.assertTrue('Please provide a valid location for the '
                                '"--sshkeyfile" argument.'
                                in cred_out.getvalue())

    def test_edit_cred_none(self):
        """Testing the edit credential command for none existing credential."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=cred_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred_none', username='root',
                             filename=TMP_KEY,
                             password=None, become_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue('credential "cred_none" does not exist'
                                    in cred_out.getvalue())

    def test_edit_cred_ssl_err(self):
        """Testing the edit credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             filename=TMP_KEY,
                             password=None, become_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aec.main(args)
                    self.assertEqual(cred_out.getvalue(), SSL_ERROR_MSG)

    def test_edit_cred_conn_err(self):
        """Testing the edit credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='credential1', username='root',
                             filename=TMP_KEY,
                             password=None, become_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aec.main(args)
                    self.assertEqual(cred_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_edit_host_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1', 'cred_type': NETWORK_CRED_TYPE,
                    'username': 'root',
                    'password': '********'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root', filename=TMP_KEY,
                             password=None, become_password=None,
                             ssh_passphrase=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')

    def test_partial_edit_host_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1', 'cred_type': NETWORK_CRED_TYPE,
                    'username': 'root'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root', filename=TMP_KEY,
                             password=None, become_password=None,
                             ssh_passphrase=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')

    def test_edit_vcenter_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1',
                    'cred_type': VCENTER_CRED_TYPE, 'username': 'root',
                    'password': '********'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root',
                             password=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')

    def test_partial_edit_vcenter_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1',
                    'cred_type': VCENTER_CRED_TYPE,
                    'password': '********'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root',
                             password=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')

    def test_edit_cred_get_error(self):
        """Testing the edit credential command server error occurs."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        results = ['Error 500']
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=500, json=results)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root', filename=TMP_KEY,
                             password=None, become_password=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    aec.main(args)
                    self.assertEqual(cred_out.getvalue(),
                                     messages.SERVER_INTERNAL_ERROR)

    def test_edit_sat_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1',
                    'cred_type': SATELLITE_CRED_TYPE, 'username': 'root',
                    'password': '********'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root',
                             password=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')

    def test_partial_edit_sat_cred(self):
        """Testing the edit credential command successfully."""
        cred_out = StringIO()
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + '1/'
        results = [{'id': 1, 'name': 'cred1',
                    'cred_type': SATELLITE_CRED_TYPE,
                    'password': '********'}]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get, status_code=200, json=data)
            mocker.patch(url_patch, status_code=200)
            aec = CredEditCommand(SUBPARSER)
            args = Namespace(name='cred1', username='root',
                             password=None)
            with redirect_stdout(cred_out):
                aec.main(args)
                self.assertEqual(cred_out.getvalue(),
                                 messages.CRED_UPDATED % 'cred1' + '\n')
