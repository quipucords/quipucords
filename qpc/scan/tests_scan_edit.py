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
from qpc.cli import CLI
from qpc.scan import SCAN_URI
from qpc.scan.edit import ScanEditCommand
from qpc.source import SOURCE_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

TMP_HOSTFILE = '/tmp/testhostsfile'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class SourceEditCliTests(unittest.TestCase):
    """Class for testing the source edit commands for qpc."""

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

    def test_edit_req_args_err(self):
        """Testing the edit command required flags."""
        source_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(source_out):
                sys.argv = ['/bin/qpc', 'scan', 'edit',
                            '--name', 'scan1']
                CLI().main()
                self.assertEqual(source_out.getvalue(),
                                 'No arguments provided to edit '
                                 'scan scan1')

    def test_edit_scan_none(self):
        """Testing the edit scan command for non-existing scan."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + '?name=scan_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan_none', sources=['source1'])
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue(messages.SCAN_DOES_NOT_EXIST % 'scan_none'
                                    in scan_out.getvalue())

    def test_edit_scan_source(self):
        """Testing the edit scan source command successfully."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + \
            '?name=source1'
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        source_results = [{'id': 1, 'name': 'source1', 'cred': 'cred1',
                           'hosts': ['1.2.3.4']}]
        source_data = {'count': 1, 'results': source_results}
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source2']}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.patch(url_patch, status_code=200, json=scan_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=['source1'],
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=None,
                             ext_product_search_dirs=None)
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    def test_partial_edit_scan_source(self):
        """Testing the edit scan source command successfully."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + \
            '?name=source1'
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        source_results = [{'id': 1, 'name': 'source1', 'cred': 'cred1',
                           'hosts': ['1.2.3.4']}]
        source_data = {'count': 1, 'results': source_results}
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source2']}
        updated_entry = {'id': 1, 'name': 'scan1', 'max_concurrency': 30}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=['source1'],
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=None,
                             ext_product_search_dirs=None)
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    def test_edit_scan_ext_products(self):
        """Testing the edit scanvcommand with enabled products successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        updated_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1'],
                         'options': {'enabled_extended_product_search':
                                     {'jboss_eap': True,
                                      'jboss_fuse': False,
                                      'jboss_brms': True}}}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=None,
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=['jboss_eap',
                                                         'jboss_brms'],
                             ext_product_search_dirs=None)
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    def test_edit_scan_search_dirs(self):
        """Testing the edit scan command with search dirs successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        updated_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1'],
                         'options': {'enabled_extended_product_search':
                                     {'search_directories': '/foo/bar/'}}}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=None,
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=None,
                             ext_product_search_dirs='/foo/bar/')
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    # pylint: disable=invalid-name
    def test_edit_scan_reset_ext_products(self):
        """Testing the edit scan command with reset successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        updated_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1'],
                         'options': {'enabled_extended_product_search':
                                     {'jboss_eap': False,
                                      'jboss_fuse': False,
                                      'jboss_brms': False}}}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=None,
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=[],
                             ext_product_search_dirs=None)
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    # pylint: disable=invalid-name
    def test_edit_scan_reset_search_dirs(self):
        """Testing the edit scan command with reset successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        updated_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1'],
                         'options': {'enabled_extended_product_search':
                                     {'jboss_eap': False,
                                      'jboss_fuse': False,
                                      'jboss_brms': False}}}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=None,
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=None,
                             ext_product_search_dirs=[])
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    # pylint: disable=invalid-name
    def test_edit_scan_reset_dis_products(self):
        """Testing the edit scan command with reset successfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        url_patch = get_server_location() + SCAN_URI + '1/'
        scan_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1']}
        updated_entry = {'id': 1, 'name': 'scan1', 'sources': ['source1'],
                         'options': {'disabled_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}}}
        results = [scan_entry]
        scan_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.patch(url_patch, status_code=200, json=updated_entry)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=None,
                             max_concurrency=50,
                             disabled_optional_products=[],
                             enabled_ext_product_search=None,
                             ext_product_search_dirs=None)
            with redirect_stdout(scan_out):
                aec.main(args)
                self.assertEqual(scan_out.getvalue(),
                                 messages.SCAN_UPDATED % 'scan1' + '\n')

    def test_edit_scan_no_val(self):
        """Testing the edit scan command with a scan that doesn't exist."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI + '?name=scan1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=500, json=None)
            aec = ScanEditCommand(SUBPARSER)
            args = Namespace(name='scan1', sources=['source1'],
                             max_concurrency=50,
                             disabled_optional_products=None,
                             enabled_ext_product_search=None,
                             ext_product_search_dirs=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    aec.main(args)
                    self.assertEqual(scan_out.getvalue(),
                                     messages.SERVER_INTERNAL_ERROR)
