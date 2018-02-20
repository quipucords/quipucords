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
import qpc.messages as messages
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout, DEFAULT_CONFIG
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.source import SOURCE_URI
from qpc.scan.add import ScanAddCommand
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ScanAddCliTests(unittest.TestCase):
    """Class for testing the scan add commands for qpc."""

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

    def test_add_req_args_err(self):
        """Testing the scan add command required flags."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'scan', 'add', '--name', 'scan1']
            CLI().main()

    def test_scan_source_none(self):
        """Testing the scan add command for none existing source."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(sources=['source_none'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    ssc.main(args)
                    self.assertTrue('Source "source_none" does not exist'
                                    in scan_out.getvalue())

    def test_add_scan_ssl_err(self):
        """Testing the add scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(sources=['source1'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(), SSL_ERROR_MSG)

    def test_add_scan_conn_err(self):
        """Testing the add scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(sources=['source1'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_add_scan_bad_resp(self):
        """Testing the add scan command successfully."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_post = get_server_location() + SCAN_URI
        results = [{'id': 1,
                    'name': 'scan1',
                    'sources': ['source1'],
                    'max-concurrency': 50}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=source_data)
            mocker.post(url_post, status_code=201, json={'id': 1})
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(sources=['source1'], max_concurrency=50)
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    ssc.main(args)
                    self.assertTrue('Source "source1" does not exist'
                                    in scan_out.getvalue())

    def test_add_scan(self):
        """Testing the add scan command successfully."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_post = get_server_location() + SCAN_URI
        results = [{'id': 1, 'name': 'scan1', 'sources': ['source1'],
                    'disable-optional-products': {'jboss-eap': False,
                                                  'jboss-fuse': False,
                                                  'jboss-brms': False}}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={'name': 'scan1'})
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=['source1'],
                             max_concurrency=50,
                             disable_optional_products={'jboss-eap': False,
                                                        'jboss-fuse': False,
                                                        'jboss-brms': False})
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_ADDED % 'scan1' + '\n')

    def test_disable_optional_products(self):
        """Testing that the disable-optional-products flag works correctly."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_post = get_server_location() + SCAN_URI
        results = [{'id': 1, 'name': 'scan1',
                    'sources': ['source1'],
                    'max-concurrency': 4,
                    'disable_optional_products': ['jboss-fuse']}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={'name': 'scan1'})
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(name='scan1',
                             sources=['source1'],
                             max_concurrency=50,
                             disable_optional_products={'jboss-eap': True,
                                                        'jboss-fuse': False,
                                                        'jboss-brms': True})
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_ADDED % 'scan1' + '\n')

    # pylint: disable=invalid-name
    def test_disable_optional_products_empty(self):
        """Testing that the disable-optional-products flag works correctly."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_post = get_server_location() + SCAN_URI
        results = [{'id': 1, 'name': 'scan1', 'sources': ['source1']}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={'name': 'scan1'})
            ssc = ScanAddCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=['source1'],
                             max_concurrency=50,
                             disable_optional_products=None)
            with redirect_stdout(scan_out):
                ssc.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_ADDED % 'scan1' + '\n')
