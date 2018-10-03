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
from unittest.mock import ANY, patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.scan.list import ScanListCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanListCliTests(unittest.TestCase):
    """Class for testing the scan list commands for qpc."""

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

    def test_list_scan_ssl_err(self):
        """Testing the list scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    slc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_list_scan_conn_err(self):
        """Testing the list scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    slc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_list_scan_internal_err(self):
        """Testing the list scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    slc.main(args)
                    self.assertEqual(scan_out.getvalue(), 'Server Error')

    def test_list_scan_empty(self):
        """Testing the list scan command successfully with empty data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(scan_out):
                slc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_LIST_NO_SCANS + '\n')

    @patch('builtins.input', return_value='yes')
    def test_list_scan_data(self, b_input):
        """Testing the list scan command successfully with stubbed data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        scan_entry = {'id': 1,
                      'scan_type': 'inspect',
                      'source': {
                          'id': 1,
                          'name': 'scan1'}}
        results = [scan_entry]
        next_link = get_server_location() + SCAN_URI + '?page=2'
        data = {
            'count': 1,
            'next': next_link,
            'results': results
        }
        data2 = {
            'count': 1,
            'next': None,
            'results': results
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(next_link, status_code=200, json=data2)
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(scan_out):
                slc.main(args)
                expected = '[{"id":1,"scan_type":"inspect"' \
                           ',"source":{"id":1,"name":"scan1"}'\
                           '}]'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(),
                                 expected + expected)
                b_input.assert_called_with(ANY)

    def test_list_filter_type(self):
        """Testing the list scan with filter by type."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        scan_entry = {'id': 1,
                      'scan_type': 'inspect',
                      'source': {
                          'id': 1,
                          'name': 'scan1'}}
        results = [scan_entry]
        data = {
            'count': 1,
            'next': None,
            'results': results
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            slc = ScanListCommand(SUBPARSER)
            args = Namespace(type='inspect')
            with redirect_stdout(scan_out):
                slc.main(args)
                expected = '[{"id":1,"scan_type":"inspect"' \
                           ',"source":{"id":1,"name":"scan1"}'\
                           '}]'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
