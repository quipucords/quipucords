#!/usr/bin/env python
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

import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.scan.clear import ScanClearCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanClearCliTests(unittest.TestCase):
    """Class for testing the scan clear commands for qpc."""

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

    def test_clear_scan_ssl_err(self):
        """Testing the clear scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + '?name=scan1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_clear_scan_conn_err(self):
        """Testing the clear scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + '?name=scan1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_clear_scan_internal_err(self):
        """Testing the clear scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + '?name=scan1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    self.assertEqual(scan_out.getvalue(), 'Server Error')

    def test_clear_scan_empty(self):
        """Testing the clear scan command successfully with empty data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + '?name=scan1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     'scan "scan1" was not found\n')

    def test_clear_by_name(self):
        """Testing the clear scan command.

        Successfully with stubbed data when specifying a name
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI + '?name=scan1'
        delete_url = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        results = [scan_entry]
        data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with redirect_stdout(scan_out):
                ncc.main(args)
                expected = messages.SCAN_REMOVED % 'scan1' + '\n'
                self.assertEqual(scan_out.getvalue(), expected)

    def test_clear_by_name_err(self):
        """Test the clear scan command successfully.

        With stubbed data when specifying a name with an error response
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI + '?name=scan1'
        delete_url = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        results = [scan_entry]
        data = {'count': 1, 'results': results}
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    expected = 'Failed to remove scan "scan1"'
                    self.assertTrue(expected in scan_out.getvalue())

    def test_clear_all_empty(self):
        """Test the clear scan command successfully.

        With stubbed data empty list of scans
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={'count': 0})
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    expected = 'No scans exist to be removed\n'
                    self.assertEqual(scan_out.getvalue(), expected)

    def test_clear_all_with_error(self):
        """Testing the clear scan command successfully.

        With stubbed data list of scans with delete error
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI
        delete_url = get_server_location() + SCAN_URI + '1/'
        delete_url2 = get_server_location() + SCAN_URI + '2/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        scan_entry2 = {'id': 2, 'name': 'scan2', 'sources': ['source1']}
        results = [scan_entry, scan_entry2]
        data = {'count': 2, 'results': results}
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            mocker.delete(delete_url2, status_code=204)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ncc.main(args)
                    expected = 'Some scans were removed, however and' \
                               ' error occurred removing the following' \
                               ' credentials:'
                    self.assertTrue(expected in scan_out.getvalue())

    def test_clear_all(self):
        """Testing the clear scan command successfully with stubbed data."""
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI
        delete_url = get_server_location() + SCAN_URI + '1/'
        delete_url2 = get_server_location() + SCAN_URI + '2/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        scan_entry2 = {'id': 2, 'name': 'scan2', 'sources': ['source1']}
        results = [scan_entry, scan_entry2]
        data = {'count': 2, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            mocker.delete(delete_url2, status_code=204)
            ncc = ScanClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with redirect_stdout(scan_out):
                ncc.main(args)
                expected = messages.SCAN_CLEAR_ALL_SUCCESS + '\n'
                self.assertEqual(scan_out.getvalue(), expected)
