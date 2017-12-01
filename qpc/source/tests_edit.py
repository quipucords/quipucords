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
import os
import sys
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.utils import read_in_file
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.credential import CREDENTIAL_URI
from qpc.source import SOURCE_URI
from qpc.source.edit import SourceEditCommand
from qpc.utils import get_server_location, write_server_config

TMP_HOSTFILE = '/tmp/testhostsfile'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class SourceEditCliTests(unittest.TestCase):
    """Class for testing the source edit commands for qpc."""

    def setUp(self):
        """Create test setup."""
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
                        '--hosts', TMP_HOSTFILE, '--credential', 'credential1']
            CLI().main()

    def test_read_input(self):
        """Test the input reading mechanism."""
        vals = read_in_file(TMP_HOSTFILE)
        expected = ['1.2.3.4', '1.2.3.[1:10]']
        self.assertEqual(expected, vals)

    def test_edit_source_none(self):
        """Testing the edit credential command for none existing credential."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source_none', hosts=['1.2.3.4'],
                             credential=['credential1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue('Source "source_none" does not exist'
                                    in source_out.getvalue())

    def test_edit_source_ssl_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(), SSL_ERROR_MSG)

    def test_edit_source_conn_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_edit_source(self):
        """Testing the edit source command successfully."""
        source_out = StringIO()
        url_get_cred = BASE_URL + CREDENTIAL_URI + '?name=credential1'
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        url_patch = BASE_URL + SOURCE_URI + '1/'
        cred_data = [{'id': 1, 'name': 'credential1', 'username': 'root',
                      'password': '********'}]
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1'], ssh_port=22)
            with redirect_stdout(source_out):
                aec.main(args)
                self.assertEqual(source_out.getvalue(),
                                 'Source "source1" was updated\n')

    def test_edit_source_no_val(self):
        """Testing the edit source command with source doesn't exist."""
        source_out = StringIO()
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=[])
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertEqual(source_out.getvalue(),
                                     'Source "source1" does not exist\n')

    def test_edit_source_cred_nf(self):
        """Testing the edit source command where credential is not found."""
        source_out = StringIO()
        url_get_cred = BASE_URL + CREDENTIAL_URI + '?name=credential1%2Ccred2'
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        cred_data = [{'id': 1, 'name': 'credential1', 'username': 'root',
                      'password': '********'}]
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1', 'cred2'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--credential" input'
                                    in source_out.getvalue())

    def test_edit_source_cred_err(self):
        """Testing the edit source command where credential request hits error."""
        source_out = StringIO()
        url_get_cred = BASE_URL + CREDENTIAL_URI + '?name=credential1%2Ccred2'
        url_get_source = BASE_URL + SOURCE_URI + '?name=source1'
        source_data = [{'id': 1, 'name': 'source1', 'hosts': ['1.2.3.4'],
                        'credentials':[{'id': 2, 'name': 'cred2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=500)
            aec = SourceEditCommand(SUBPARSER)
            args = Namespace(name='source1', hosts=['1.2.3.4'],
                             credential=['credential1', 'cred2'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(source_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--credential" input'
                                    in source_out.getvalue())
