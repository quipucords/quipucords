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
from qpc.network.clear import NetworkClearCommand

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class NetworkClearCliTests(unittest.TestCase):
    """Class for testing the profile clear commands for qpc."""

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

    def test_clear_network_ssl_err(self):
        """Testing the clear profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    self.assertEqual(network_out.getvalue(), SSL_ERROR_MSG)

    def test_clear_network_conn_err(self):
        """Testing the clear profile command with a connection error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     CONNECTION_ERROR_MSG)

    def test_clear_network_internal_err(self):
        """Testing the clear profile command with an internal error."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={'error': ['Server Error']})
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    self.assertEqual(network_out.getvalue(), 'Server Error')

    def test_clear_network_empty(self):
        """Testing the clear profile command successfully with empty data."""
        network_out = StringIO()
        url = BASE_URL + NETWORK_URI + '?name=profile1'
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=[])
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    self.assertEqual(network_out.getvalue(),
                                     'Profile "profile1" was not found\n')

    def test_clear_by_name(self):
        """Testing the clear profile command.

        Successfully with stubbed data when specifying a name
        """
        network_out = StringIO()
        get_url = BASE_URL + NETWORK_URI + '?name=profile1'
        delete_url = BASE_URL + NETWORK_URI + '1/'
        profile_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'auth': ['auth1', 'auth2'], 'ssh_port': 22}
        data = [profile_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with redirect_stdout(network_out):
                ncc.main(args)
                expected = 'Profile "profile1" was removed\n'
                self.assertEqual(network_out.getvalue(), expected)

    def test_clear_by_name_err(self):
        """Test the clear profile command successfully.

        With stubbed data when specifying a name with an error response
        """
        network_out = StringIO()
        get_url = BASE_URL + NETWORK_URI + '?name=profile1'
        delete_url = BASE_URL + NETWORK_URI + '1/'
        profile_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'auth': ['auth1', 'auth2'], 'ssh_port': 22}
        data = [profile_entry]
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name='profile1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    expected = 'Failed to remove profile "profile1"'
                    self.assertTrue(expected in network_out.getvalue())

    def test_clear_all_empty(self):
        """Test the clear profile command successfully.

        With stubbed data empty list of profiles
        """
        network_out = StringIO()
        get_url = BASE_URL + NETWORK_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=[])
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    expected = 'No profiles exist to be removed\n'
                    self.assertEqual(network_out.getvalue(), expected)

    def test_clear_all_with_error(self):
        """Testing the clear profile command successfully.

        With stubbed data list of profiles with delete error
        """
        network_out = StringIO()
        get_url = BASE_URL + NETWORK_URI
        delete_url = BASE_URL + NETWORK_URI + '1/'
        profile_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'auth': ['auth1', 'auth2'], 'ssh_port': 22}
        data = [profile_entry]
        err_data = {'error': ['Server Error']}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(network_out):
                    ncc.main(args)
                    expected = 'Some profiles were removed, however and' \
                               ' error occurred removing the following' \
                               ' credentials:'
                    self.assertTrue(expected in network_out.getvalue())

    def test_clear_all(self):
        """Testing the clear profile command successfully with stubbed data."""
        network_out = StringIO()
        get_url = BASE_URL + NETWORK_URI
        delete_url = BASE_URL + NETWORK_URI + '1/'
        profile_entry = {'id': 1, 'name': 'profile1', 'hosts': ['1.2.3.4'],
                         'auth': ['auth1', 'auth2'], 'ssh_port': 22}
        data = [profile_entry]
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            ncc = NetworkClearCommand(SUBPARSER)
            args = Namespace(name=None)
            with redirect_stdout(network_out):
                ncc.main(args)
                expected = 'All profiles were removed\n'
                self.assertEqual(network_out.getvalue(), expected)
