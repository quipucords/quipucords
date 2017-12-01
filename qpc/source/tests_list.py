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
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.list import SourceListCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class SourceListCliTests(unittest.TestCase):
    """Class for testing the source list commands for qpc."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_list_source_ssl_err(self):
        """Testing the list source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            nlc = SourceListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nlc.main(args)
                    self.assertEqual(source_out.getvalue(), SSL_ERROR_MSG)

    def test_list_source_conn_err(self):
        """Testing the list source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            nlc = SourceListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nlc.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_list_source_internal_err(self):
        """Testing the list source command with an internal error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            nlc = SourceListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nlc.main(args)
                    self.assertEqual(source_out.getvalue(), 'Server Error')

    def test_list_source_empty(self):
        """Testing the list source command successfully with empty data."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            nlc = SourceListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(source_out):
                nlc.main(args)
                self.assertEqual(source_out.getvalue(),
                                 'No sources exist yet.\n')

    def test_list_source_data(self):
        """Testing the list source command successfully with stubbed data."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI
        auth_entry = {'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                      'credentials': [{'id': 1, 'name': 'auth1'}]}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            nlc = SourceListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(source_out):
                nlc.main(args)
                expected = '[{"credentials":[{"id":1,"name":"auth1"}],' \
                    '"hosts":["1.2.3.4"],"id":1,"name":"source1"}]'
                self.assertEqual(source_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
