#
# Copyright (c) 2018 Red Hat, Inc.
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
from qpc.tests_utilities import HushUpStderr, redirect_stdout, DEFAULT_CONFIG
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_JOB_URI
from qpc.scan.status import ScanStatusCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanStatusCliTests(unittest.TestCase):
    """Class for testing the scan status commands for qpc."""

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

    def test_status_scan_ssl_err(self):
        """Testing the scan status command with SSL error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + '1/'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            nsc = ScanStatusCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_status_scan_conn_err(self):
        """Testing the scan status command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + '1/'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            nsc = ScanStatusCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_status_scan_internal_err(self):
        """Testing the scan status command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + '1/'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            nsc = ScanStatusCommand(SUBPARSER)
            args = Namespace(id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), 'Server Error')

    # pylint: disable=invalid-name
    def test_status_scan_data_multiple_scans(self):
        """Testing the scan status command successfully with stubbed data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI
        get_url = get_server_location() + SCAN_JOB_URI + '1/'
        scan_entry = {'id': 1, 'status': 'running'}
        scan_entry2 = {'id': 2, 'status': 'completed'}
        results = [scan_entry, scan_entry2]
        data = {'count': 2, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(get_url, status_code=200, json=scan_entry)
            nsc = ScanStatusCommand(SUBPARSER)
            args = Namespace(id='1')
            with redirect_stdout(scan_out):
                nsc.main(args)
                expected = 'Scanjob"1":"running".'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)

    def test_status_scan_data_one_scan(self):
        """Testing the scan status command successfully with stubbed data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI
        get_url = get_server_location() + SCAN_JOB_URI + '1/'
        scan_entry = {'id': 1, 'status': 'paused'}
        results = [scan_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(get_url, status_code=200, json=scan_entry)
            nsc = ScanStatusCommand(SUBPARSER)
            args = Namespace(id='1')
            with redirect_stdout(scan_out):
                nsc.main(args)
                expected = 'Scanjob"1":"paused".'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
