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
"""Test the CLI module"""

import unittest
import sys
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests
import requests_mock
from cli.tests_utilities import HushUpStderr, redirect_stdout
from cli.request import BASE_URL, CONNECTION_ERROR_MSG, SSL_ERROR_MSG
from cli.network import NETWORK_URI
from cli.network.list import NetworkListCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class NetworkListCliTests(unittest.TestCase):
    """Class for testing the network list commands for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_list_network_ssl_err(self):
        """Testing the list network command with a connection error
        """
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            nlc = NetworkListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nlc.main(args)
                    self.assertEqual(network_out.getvalue(), SSL_ERROR_MSG)

    def test_list_network_conn_err(self):
        """Testing the list network command with a connection error
        """
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            nlc = NetworkListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nlc.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_list_network_internal_err(self):
        """Testing the list network command with an internal error
        """
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            nlc = NetworkListCommand(SUBPARSER)
            args = Namespace()
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    nlc.main(args)
                    self.assertEqual(network_out.getvalue(), 'Server Error')

    def test_list_network_empty(self):
        """Testing the list network command successfully with empty data
        """
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            nlc = NetworkListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(network_out):
                nlc.main(args)
                self.assertEqual(network_out.getvalue(),
                                 'No profiles exist yet.\n')

    def test_list_network_data(self):
        """Testing the list network command successfully with stubbed data
        """
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI
        auth_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                      'credentials': [{'id': 1, 'name': 'auth1'}]}
        data = [auth_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            nlc = NetworkListCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(network_out):
                nlc.main(args)
                expected = '[{"credentials":[{"id":1,"name":"auth1"}],' \
                    '"hosts":["1.2.3.4"],"id":1,"name":"profile1"}]'
                self.assertEqual(network_out.getvalue().replace('\n', '')
                                 .replace(' ', '').strip(), expected)
