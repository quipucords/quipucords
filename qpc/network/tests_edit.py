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
from qpc.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.auth import AUTH_URI
from qpc.network import NETWORK_URI
from qpc.network.edit import NetworkEditCommand

TMP_HOSTFILE = '/tmp/testhostsfile'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class NetworkEditCliTests(unittest.TestCase):
    """Class for testing the network profile edit commands for qpc."""

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
        network_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(network_out):
                sys.argv = ['/bin/qpc', 'profile', 'edit',
                            '--name', 'profile1']
                CLI().main()
                self.assertEqual(network_out.getvalue(),
                                 'No arguments provided to edit '
                                 'profile profile1')

    def test_edit_process_file(self):
        """Testing the add network command process file."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'network', 'add', '--name', 'net1',
                        '--hosts', TMP_HOSTFILE, '--auth', 'auth1']
            CLI().main()

    def test_read_input(self):
        """Test the input reading mechanism."""
        vals = read_in_file(TMP_HOSTFILE)
        expected = ['1.2.3.4', '1.2.3.[1:10]']
        self.assertEqual(expected, vals)

    def test_edit_profile_none(self):
        """Testing the edit auth command for none existing auth."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile_none'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile_none', hosts=['1.2.3.4'],
                             auth=['auth1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    aec.main(args)
                    self.assertTrue('Profile "profile_none" does not exist'
                                    in network_out.getvalue())

    def test_edit_profile_ssl_err(self):
        """Testing the edit profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    self.assertEqual(network_out.getvalue(), SSL_ERROR_MSG)

    def test_edit_profile_conn_err(self):
        """Testing the edit profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_edit_profile(self):
        """Testing the edit profile command successfully."""
        network_out = StringIO()
        url_get_auth = BASE_URL + AUTH_URI + '?name=auth1'
        url_get_network = BASE_URL + NETWORK_URI + '?name=profile1'
        url_patch = BASE_URL + NETWORK_URI + '1/'
        auth_data = [{'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}]
        network_data = [{'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'credentials':[{'id': 2, 'name': 'auth2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_network, status_code=200, json=network_data)
            mocker.get(url_get_auth, status_code=200, json=auth_data)
            mocker.patch(url_patch, status_code=200)
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1'], ssh_port=22)
            with redirect_stdout(network_out):
                aec.main(args)
                self.assertEqual(network_out.getvalue(),
                                 'Profile "profile1" was updated\n')

    def test_edit_profile_no_val(self):
        """Testing the edit profile command with profile doesn't exist."""
        network_out = StringIO()
        url_get_network = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_network, status_code=500, json=[])
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     'Profile "profile1" does not exist\n')

    def test_edit_profile_auth_nf(self):
        """Testing the edit profile command where auth is not found."""
        network_out = StringIO()
        url_get_auth = BASE_URL + AUTH_URI + '?name=auth1%2Cauth2'
        url_get_network = BASE_URL + NETWORK_URI + '?name=profile1'
        auth_data = [{'id': 1, 'name': 'auth1', 'username': 'root',
                      'password': '********'}]
        network_data = [{'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'credentials':[{'id': 2, 'name': 'auth2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_network, status_code=200, json=network_data)
            mocker.get(url_get_auth, status_code=200, json=auth_data)
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1', 'auth2'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--auth" input'
                                    in network_out.getvalue())

    def test_edit_profile_auth_err(self):
        """Testing the edit profile command where auth request hits error."""
        network_out = StringIO()
        url_get_auth = BASE_URL + AUTH_URI + '?name=auth1%2Cauth2'
        url_get_network = BASE_URL + NETWORK_URI + '?name=profile1'
        network_data = [{'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'credentials':[{'id': 2, 'name': 'auth2'}]}]
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_network, status_code=200, json=network_data)
            mocker.get(url_get_auth, status_code=500)
            aec = NetworkEditCommand(SUBPARSER)
            args = Namespace(name='profile1', hosts=['1.2.3.4'],
                             auth=['auth1', 'auth2'], ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    aec.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--auth" input'
                                    in network_out.getvalue())
