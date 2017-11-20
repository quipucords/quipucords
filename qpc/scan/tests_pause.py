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
from qpc.scan import SCAN_URI
from qpc.scan.pause import ScanPauseCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class ScanPauseCliTests(unittest.TestCase):
    """Class for testing the scan pause commands for qpc."""

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

    def test_pause_scan_ssl_err(self):
        """Testing the pause scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI + '1/pause/'
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.SSLError)
            nsc = ScanPauseCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_pause_scan_conn_err(self):
        """Testing the pause scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI + '1/pause/'
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.ConnectTimeout)
            nsc = ScanPauseCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_pause_scan_internal_err(self):
        """Testing the pause scan command with an internal error."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI + '1/pause/'
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=500, json={'error': ['Server Error']})
            nsc = ScanPauseCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), 'Server Error')

    def test_pause_scan_data(self):
        """Testing the pause scan command successfully with stubbed data."""
        scan_out = StringIO()
        url = BASE_URL + SCAN_URI + '1/pause/'
        scan_entry = {'id': 1,
                      'profile': {
                          'id': 1,
                          'name': 'scan1'},
                      'scan_type': 'host',
                      'status': 'completed'}
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200, json=scan_entry)
            nsc = ScanPauseCommand(SUBPARSER)
            args = Namespace(id='1')
            with redirect_stdout(scan_out):
                nsc.main(args)
                expected = 'Scan "1" paused\n'
                self.assertEqual(scan_out.getvalue(), expected)
