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

from qpc.cred import CREDENTIAL_URI
from qpc.cred.show import CredShowCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock


PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class CredentialShowCliTests(unittest.TestCase):
    """Class for testing the credential show commands for qpc."""

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

    def test_show_cred_ssl_err(self):
        """Testing the show credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            csc = CredShowCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    csc.main(args)

    def test_show_cred_conn_err(self):
        """Testing the show credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            csc = CredShowCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    csc.main(args)

    def test_show_cred_internal_err(self):
        """Testing the show credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=credential1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            csc = CredShowCommand(SUBPARSER)
            args = Namespace(name='credential1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    csc.main(args)

    def test_show_cred_empty(self):
        """Testing the show credential command successfully with empty data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=cred1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            csc = CredShowCommand(SUBPARSER)
            args = Namespace(name='cred1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(cred_out):
                    csc.main(args)

    def test_show_cred_data(self):
        """Testing the show credential command with stubbed data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + '?name=cred1'
        credential_entry = {'id': 1, 'name': 'cred1', 'username': 'root',
                            'password': '********'}
        results = [credential_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            csc = CredShowCommand(SUBPARSER)
            args = Namespace(name='cred1')
            with redirect_stdout(cred_out):
                csc.main(args)
                expected = '{"id":1,"name":"cred1","password":"********",' \
                    '"username":"root"}'
                self.assertEqual(cred_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
