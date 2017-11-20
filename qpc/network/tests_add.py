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
from argparse import ArgumentParser, Namespace, ArgumentTypeError
import requests
import requests_mock
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.auth import AUTH_URI
from qpc.network import NETWORK_URI
from qpc.network.add import NetworkAddCommand
from qpc.network.utils import validate_port
from qpc.utils import get_server_location, write_server_config

TMP_HOSTFILE = '/tmp/testhostsfile'
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')

write_server_config({'host': '127.0.0.1', 'port': 8000})
BASE_URL = get_server_location()


class NetworkAddCliTests(unittest.TestCase):
    """Class for testing the network profile add commands for qpc."""

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
        """Remove test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        if os.path.isfile(TMP_HOSTFILE):
            os.remove(TMP_HOSTFILE)

    def test_add_req_args_err(self):
        """Testing the add network command required flags."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'network', 'add', '--name', 'net1']
            CLI().main()

    def test_add_process_file(self):
        """Testing the add network command process file."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'network', 'add', '--name', 'net1',
                        '--hosts', TMP_HOSTFILE, '--auth', 'auth1']
            CLI().main()

    def test_validate_port_string(self):
        """Testing the add network command with port validation non-integer."""
        net_out = StringIO()
        with self.assertRaises(ArgumentTypeError):
            with redirect_stdout(net_out):
                validate_port('ff')
                self.assertTrue('Port value ff'
                                in net_out.getvalue())

    def test_validate_port_bad_type(self):
        """Testing the add network command with port validation bad type."""
        net_out = StringIO()
        with self.assertRaises(ArgumentTypeError):
            with redirect_stdout(net_out):
                validate_port(['ff'])
                self.assertTrue('Port value ff'
                                in net_out.getvalue())

    def test_validate_port_range_err(self):
        """Test the add network command with port validation out of range."""
        net_out = StringIO()
        with self.assertRaises(ArgumentTypeError):
            with redirect_stdout(net_out):
                validate_port('65537')
                self.assertTrue('Port value 65537'
                                in net_out.getvalue())

    def test_validate_port_good(self):
        """Testing the add network command with port validation success."""
        val = validate_port('80')
        self.assertEqual(80, val)

    def test_add_network_name_dup(self):
        """Testing the add network command duplicate name."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1'
        get_auth_data = [{'id': 1, 'name': 'auth1'}]
        post_network_url = BASE_URL + NETWORK_URI
        error = {'name': ['profile with this name already exists.']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, status_code=200, json=get_auth_data)
            mocker.post(post_network_url, status_code=400, json=error)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net_dup', auth=['auth1'], hosts=['1.2.3.4'],
                             ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(net_out):
                    nac.main(args)
                    nac.main(args)
                    self.assertTrue('profile with this name already exists.'
                                    in net_out.getvalue())

    def test_add_network_auth_less(self):
        """Testing the add network command with a some invalid auth."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1%2Cauth2'
        get_auth_data = [{'id': 1, 'name': 'auth1'}]
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, status_code=200, json=get_auth_data)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net1', auth=['auth1', 'auth2'],
                             hosts=['1.2.3.4'],
                             ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(net_out):
                    nac.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--auth" input'
                                    in net_out.getvalue())

    def test_add_network_auth_err(self):
        """Testing the add network command with an auth err."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1%2Cauth2'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, status_code=500)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net1', auth=['auth1', 'auth2'],
                             hosts=['1.2.3.4'],
                             ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(net_out):
                    nac.main(args)
                    self.assertTrue('An error occurred while processing '
                                    'the "--auth" input'
                                    in net_out.getvalue())

    def test_add_network_ssl_err(self):
        """Testing the add network command with a connection error."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, exc=requests.exceptions.SSLError)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net1', auth=['auth1'], hosts=['1.2.3.4'],
                             ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(net_out):
                    nac.main(args)
                    self.assertEqual(net_out.getvalue(), SSL_ERROR_MSG)

    def test_add_network_conn_err(self):
        """Testing the add network command with a connection error."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, exc=requests.exceptions.ConnectTimeout)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net1', auth=['auth1'], hosts=['1.2.3.4'],
                             ssh_port=22)
            with self.assertRaises(SystemExit):
                with redirect_stdout(net_out):
                    nac.main(args)
                    self.assertEqual(net_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_add_network(self):
        """Testing the add network command successfully."""
        net_out = StringIO()
        get_auth_url = BASE_URL + AUTH_URI + '?name=auth1'
        get_auth_data = [{'id': 1, 'name': 'auth1'}]
        post_network_url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_auth_url, status_code=200, json=get_auth_data)
            mocker.post(post_network_url, status_code=201)
            nac = NetworkAddCommand(SUBPARSER)
            args = Namespace(name='net1', auth=['auth1'], hosts=['1.2.3.4'],
                             ssh_port=22)
            with redirect_stdout(net_out):
                nac.main(args)
                self.assertEqual(net_out.getvalue(),
                                 'Profile "net1" was added\n')
