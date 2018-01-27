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
import qpc.messages as messages
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.source import SOURCE_URI
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

    def test_scan_source_none(self):
        """Testing the scan start command for none existing source."""
        scan_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source_none'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    ssc.main(args)
                    self.assertTrue('Source "source_none" does not exist'
                                    in scan_out.getvalue())

    def test_start_scan_ssl_err(self):
        """Testing the start scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source1'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_start_scan_conn_err(self):
        """Testing the start scan command with a connection error."""
        scan_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source1'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_start_scan_bad_resp(self):
        """Testing the start scan command successfully."""
        scan_out = StringIO()
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        url_post = BASE_URL + SCAN_URI
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=source_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source1'], max_concurrency=4,
                             disable_optional_products={'jboss-eap': True,
                                                        'jboss-fuse': True,
                                                        'jboss-brms': True})
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertTrue('Source "source_none" does not exist'
                                    in scan_out.getvalue())

    def test_start_scan(self):
        """Testing the start scan command successfully."""
        scan_out = StringIO()
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        url_post = BASE_URL + SCAN_URI
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source1'], max_concurrency=4,
                             disable_optional_products={'jboss-eap': True,
                                                        'jboss-fuse': True,
                                                        'jboss-brms': True})
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_STARTED % '1' + '\n')

    def test_disable_optional_products(self):
        """Testing that the disable-optional-products flag works correctly."""
        scan_out = StringIO()
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        url_post = BASE_URL + SCAN_URI
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}],
                        'disable_optional_products': ['jboss-fuse']}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanStartCommand(SUBPARSER)
            args = Namespace(sources=['source1'], max_concurrency=4,
                             disable_optional_products={'jboss-eap': True,
                                                        'jboss-fuse': False,
                                                        'jboss-brms': True})
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_STARTED % '1' + '\n')
