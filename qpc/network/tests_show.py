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
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from qpc.network import NETWORK_URI
from qpc.network.show import NetworkShowCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class NetworkShowCliTests(unittest.TestCase):
    """Class for testing the profile show commands for qpc."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_show_network_ssl_err(self):
        """Testing the show profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            nsc = NetworkShowCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nsc.main(args)
                    self.assertEqual(network_out.getvalue(), SSL_ERROR_MSG)

    def test_show_network_conn_err(self):
        """Testing the show profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            nsc = NetworkShowCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nsc.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_show_network_internal_err(self):
        """Testing the show profile command with an internal error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            nsc = NetworkShowCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nsc.main(args)
                    self.assertEqual(network_out.getvalue(), 'Server Error')

    def test_show_network_empty(self):
        """Testing the show profile command successfully with empty data."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            nsc = NetworkShowCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nsc.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     'Profile "profile1" does not exist\n')

    def test_show_network_data(self):
        """Testing the show profile command successfully with stubbed data."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        auth_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                      'credentials': [{'id': 1, 'name': 'auth1'}]}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            nsc = NetworkShowCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with redirect_stdout(network_out):
                nsc.main(args)
                expected = '{"credentials":[{"id":1,"name":"auth1"}],' \
                    '"hosts":["1.2.3.4"],"id":1,"name":"profile1"}'
                self.assertEqual(network_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
