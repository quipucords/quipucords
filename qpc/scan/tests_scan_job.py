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
from qpc.scan import SCAN_URI, SCAN_JOB_URI
from qpc.scan.job import ScanJobCommand
from qpc.utils import get_server_location, write_server_config
from qpc import messages

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanJobCliTests(unittest.TestCase):
    """Class for testing the scan job commands for qpc."""

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

    def test_scan_job_ssl_err(self):
        """Testing the scan job command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    sjc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_scan_job_conn_err(self):
        """Testing the scan job command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    sjc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_scan_job_internal_err(self):
        """Testing the scan job command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    sjc.main(args)
                    self.assertEqual(scan_out.getvalue(), 'Server Error')

    def test_scan_job_empty(self):
        """Testing the scan job command successfully with empty data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    sjc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     messages.SCAN_LIST_NO_SCANS + '\n')

    def test_scan_job_filter_id(self):
        """Testing the list scan with filter by id."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        # set up scan object
        scan_entry = {'id': 1,
                      'name': 'scan1',
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
        # set up scan jobs
        urlscanjob = get_server_location() + SCAN_JOB_URI + '1/'
        scan_job = {'id': 1,
                    'status': 'completed',
                    'scan': 'scan1'}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(urlscanjob, status_code=200, json=scan_job)
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1', id='1')
            with redirect_stdout(scan_out):
                sjc.main(args)
                expected = '{"id":1,"scan":"scan1","status":"completed"}'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)

    def test_scan_job_filter_status(self):
        """Testing the scan job with filter by status."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        # set up scan object
        scan_entry = {'id': 1,
                      'name': 'scan1',
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
        # set up scan jobs
        urlscanjob = url + '1/jobs/?status=completed'
        scan_job = {'count': 3,
                    'results': [{'id': 1,
                                 'status': 'completed',
                                 'scan': 'scan1'},
                                {'id': 2,
                                 'status': 'completed',
                                 'scan': 'scan1'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(urlscanjob, status_code=200, json=scan_job)
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1', status='completed')
            with redirect_stdout(scan_out):
                sjc.main(args)
                expected = '[{"id":1,"scan":"scan1","status":"completed"},' \
                           '{"id":2,"scan":"scan1","status":"completed"}]'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)

    def test_scan_job_no_filter(self):
        """Testing the scan job with only name."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        # set up scan object
        scan_entry = {'id': 1,
                      'name': 'scan1',
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
        # set up scan jobs
        urlscanjob = get_server_location() + SCAN_URI + '1/jobs/'
        scan_job = {'count': 3,
                    'results': [{'id': 1,
                                 'status': 'completed',
                                 'scan': 'scan1'},
                                {'id': 2,
                                 'status': 'running',
                                 'scan': 'scan1'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(urlscanjob, status_code=200, json=scan_job)
            sjc = ScanJobCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with redirect_stdout(scan_out):
                sjc.main(args)
                expected = '[{"id":1,"scan":"scan1","status":"completed"},' \
                           '{"id":2,"scan":"scan1","status":"running"}]'
                self.assertEqual(scan_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
