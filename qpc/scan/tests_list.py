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
from qpc.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.scan.list import ScanListCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanListCliTests(unittest.TestCase):
    """Class for testing the scan list commands for qpc."""

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

    def test_list_scan_ssl_err(self):
        """Testing the list scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI
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
        url = BASE_URL + SCAN_URI
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
        url = BASE_URL + SCAN_URI
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
        url = BASE_URL + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(scan_out):
                slc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 'No scans exist yet.\n')

    def test_list_scan_data(self):
        """Testing the list scan command successfully with stubbed data."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI
        scan_entry = {'id': 1,
                      'profile': {
                          'id': 1,
                          'name': 'scan1'},
                      'scan_type': 'host',
                      'status': 'completed'}
        data = [scan_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            slc = ScanListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(scan_out):
                slc.main(args)
                expected = '[{"id":1,"profile":{"id":1,"name":"scan1"},' \
                           '"scan_type":"host","status":"completed"}]'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
