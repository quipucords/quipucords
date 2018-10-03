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

from qpc import messages
from qpc.cli import CLI
from qpc.scan import SCAN_URI
from qpc.scan.start import ScanStartCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanStartCliTests(unittest.TestCase):
    """Class for testing the scan start commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Tear down test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_start_req_args_err(self):
        """Testing the scan start command required flags."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'scan', 'start' '--name' 'scan1']
            CLI().main()

    def test_scan_with_scan_none(self):
        """Testing the scan start command for none existing source."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + '1/'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            mocker.post(url_post, status_code=300, json=None)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(name='scan_none')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertTrue('Scan "scan_none" does not exist.'
                                    in scan_out.getvalue())

    def test_start_scan(self):
        """Testing the start scan command successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + '1/jobs/'
        results = [{'id': 1, 'name': 'scan1', 'sources': ['source1'],
                    'disable-optional-products': {'jboss-eap': False,
                                                  'jboss-fuse': False,
                                                  'jboss-brms': False}}]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_STARTED % '1' + '\n')

    def test_unsuccessful_start_scan(self):
        """Testing the start scan command unsuccessfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + '1/jobs/'
        results = [{'id': 1, 'name': 'scan1', 'sources': ['source1'],
                    'disable-optional-products': {'jboss-eap': False,
                                                  'jboss-fuse': False,
                                                  'jboss-brms': False}}]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(name='scan2')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertTrue('Scan "scan2" does not exist'
                                    in scan_out.getvalue())

    def test_start_scan_bad_resp(self):
        """Testing the start scan command with a 500 error."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=500, json=None)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(name='scan1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     messages.SERVER_INTERNAL_ERROR)
