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
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.network import NETWORK_URI
from qpc.scan.start import ScanStartCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class ScanStartCliTests(unittest.TestCase):
    """Class for testing the scan start commands for qpc."""

    def setUp(self):
        """Create test setup."""
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
            sys.argv = ['/bin/qpc', 'scan', 'start']
            CLI().main()

    def test_scan_profile_none(self):
        """Testing the scan start command for none existing profile."""
        scan_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(profile='profile_none')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    ssc.main(args)
                    self.assertTrue('Profile "profile_none" does not exist'
                                    in scan_out.getvalue())

    def test_start_scan_ssl_err(self):
        """Testing the start scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(profile='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_start_scan_conn_err(self):
        """Testing the start scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(profile='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_start_scan(self):
        """Testing the start scan command successfully."""
        scan_out = StringIO()
        url_get_network = BASE_URL + NETWORK_URI + '?name=profile1'
        url_post = BASE_URL + SCAN_URI
        network_data = [{'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'credentials':[{'id': 2, 'name': 'auth2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_network, status_code=200, json=network_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(profile='profile1', max_concurrency=4)
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 'Scan "1" started\n')
