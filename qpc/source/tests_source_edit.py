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

import os
import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.edit import SourceEditCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import (get_server_location,
                       read_in_file,
                       write_server_config)

import requests

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
        if os.path.isfile(TMP_HOSTFILE):
            os.remove(TMP_HOSTFILE)
        with open(TMP_HOSTFILE, 'w') as test_hostfile:
            test_hostfile.write('1.2.3.4\n')
            test_hostfile.write('1.2.3.[1:10]\n')

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        if os.path.isfile(TMP_HOSTFILE):
            os.remove(TMP_HOSTFILE)

    def test_edit_req_args_err(self):
        """Testing the add edit command required flags."""
        source_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(source_out):
                sys.argv = ['/bin/qpc', 'source', 'edit',
                            '--name', 'source1']
                CLI().main()
                self.assertEqual(source_out.getvalue(),
                                 'No arguments provided to edit '
                                 'source source1')

    def test_edit_process_file(self):
        """Testing the add source command process file."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'source', 'add', '--name', 'source1',
                        '--type', 'network', '--hosts', TMP_HOSTFILE,
                        '--cred', 'credential1']
            CLI().main()

    def test_read_input(self):
        """Test the input reading mechanism."""
        vals = read_in_file(TMP_HOSTFILE)
        expected = ['1.2.3.4', '1.2.3.[1:10]']
        self.assertEqual(expected, vals)

    def test_edit_source_none(self):
        """Testing the edit cred command for none existing cred."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={'count': 0})
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source_none', hosts=['1.2.3.4'],
                             cred=['credential1'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue('Source "source_none" does not exist'
                                    in source_out.getvalue())

    def test_edit_source_ssl_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             cred=['credential1'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(), SSL_ERROR_MSG)

    def test_edit_source_conn_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             cred=['credential1'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    ##################################################
    # Network Source Test
    ##################################################
    def test_edit_net_source(self):
        """Testing the edit network source command successfully."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_patch = get_server_location() + SOURCE_URI + '1/'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'exclude_hosts':['1.2.3.4.'],
                    'credentials':[{'id': 2, 'name': 'cred2'}]}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4', '2.3.4.5'],
                             excluded_hosts=['1.2.3.4'], cred=['credential1'],
                             port=22)
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 messages.SOURCE_UPDATED % 'source1' + '\n')

    def test_edit_source_exclude_host(self):
        """Testing edit network source command by adding an excluded host."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_patch = get_server_location() + SOURCE_URI + '1/'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials':[{'id': 2, 'name': 'cred2'}]}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.[0:255]'],
                             exclude_hosts=['1.2.3.4'], cred=['credential1'],
                             port=22)
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 messages.SOURCE_UPDATED % 'source1' + '\n')

    ##################################################
    # Vcenter Source Test
    ##################################################
    def test_edit_vc_source(self):
        """Testing the edit vcenter source command successfully."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_patch = get_server_location() + SOURCE_URI + '1/'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials': [{'id': 2, 'name': 'cred2'}]}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.5'],
                             cred=['credential1'])
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 messages.SOURCE_UPDATED % 'source1' + '\n')

    def test_edit_disable_ssl(self):
        """Testing that you can edit the disable-ssl arg successfully."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_patch = get_server_location() + SOURCE_URI + '1/'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials': [{'id': 2, 'name': 'cred2'}],
                    'disable_ssl': 'true'}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.5'],
                             cred=['credential1'], disable_ssl='True')
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 messages.SOURCE_UPDATED % 'source1' + '\n')

    def test_edit_ssl_protocol(self):
        """Testing that you can edit the ssl_protocol arg successfully."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        url_patch = get_server_location() + SOURCE_URI + '1/'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials': [{'id': 2, 'name': 'cred2'}],
                    'ssl_protocol': 'SSLv23'}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.5'],
                             cred=['credential1'], ssl_protocol='SSLv23')
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 messages.SOURCE_UPDATED % 'source1' + '\n')

    def test_edit_source_no_val(self):
        """Testing the edit source command with a server error."""
        source_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=None)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             cred=['credential1'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     messages.SERVER_INTERNAL_ERROR)

    def test_edit_source_cred_nf(self):
        """Testing the edit source command where cred is not found."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1%2Ccred2'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        cred_results = [{'id': 1, 'name': 'credential1', 'username': 'root',
                         'password': '********'}]
        cred_data = {'count': 1, 'results': cred_results}
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials':[{'id': 2, 'name': 'cred2'}]}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             cred=['credential1', 'cred2'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--cred" input'
                                    in source_out.getvalue())

    def test_edit_source_cred_err(self):
        """Testing the edit source command where cred request hits error."""
        source_out = StringIO()
        url_get_cred = get_server_location() + CREDENTIAL_URI + \
            '?name=credential1%2Ccred2'
        url_get_source = get_server_location() + SOURCE_URI + '?name=source1'
        results = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                    'credentials':[{'id': 2, 'name': 'cred2'}]}]
        source_data = {'count': 1, 'results': results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=500)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             cred=['credential1', 'cred2'], port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--cred" input'
                                    in source_out.getvalue())
