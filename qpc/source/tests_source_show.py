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

from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.show import SourceShowCommand
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000, 'use_http': True})
BASE_URL = get_server_location()
print(BASE_URL)


class SourceShowCliTests(unittest.TestCase):
    """Class for testing the source show commands for qpc."""

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

    def test_show_source_ssl_err(self):
        """Testing the show source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            nsc = SourceShowCommand(SUBPARSER)
            args = Namespace(name='source1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nsc.main(args)
                    self.assertEqual(source_out.getvalue(), SSL_ERROR_MSG)

    def test_show_source_conn_err(self):
        """Testing the show source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            nsc = SourceShowCommand(SUBPARSER)
            args = Namespace(name='source1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nsc.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_show_source_internal_err(self):
        """Testing the show source command with an internal error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            nsc = SourceShowCommand(SUBPARSER)
            args = Namespace(name='source1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nsc.main(args)
                    self.assertEqual(source_out.getvalue(), 'Server Error')

    def test_show_source_empty(self):
        """Testing the show source command successfully with empty data."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            nsc = SourceShowCommand(SUBPARSER)
            args = Namespace(name='source1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    nsc.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     'Source "source1" does not exist\n')

    def test_show_source_data(self):
        """Testing the show source command successfully with stubbed data."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        source_entry = {'id': 1, 'name': 'source1',
                        'hosts': ['1.2.3.4'],
                        'credentials': [{'id': 1, 'name': 'cred1'}]}
        results = [source_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            nsc = SourceShowCommand(SUBPARSER)
            args = Namespace(name='source1')
            with redirect_stdout(source_out):
                nsc.main(args)
                expected = '{"credentials":[{"id":1,"name":"cred1"}],' \
                    '"hosts":["1.2.3.4"],"id":1,"name":"source1"}'
                self.assertEqual(source_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
