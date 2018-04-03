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

import sys
import unittest
from io import StringIO

from qpc import messages
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.utils import read_server_config, write_server_config

DEFAULT_PORT = 443


class ConfigureHostTests(unittest.TestCase):
    """Class for testing the server host configuration."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test case setup."""
        # Reset server config to default ip/port
        config_out = StringIO()
        sys.argv = ['/bin/qpc', 'server', 'config',
                    '--host', '127.0.0.1', '--port', '443']

        with redirect_stdout(config_out):
            CLI().main()
            config = read_server_config()
            self.assertEqual(config['host'], '127.0.0.1')
            self.assertEqual(config['port'], 443)
            self.assertEqual(config_out.getvalue(),
                             messages.SERVER_CONFIG_SUCCESS % ('https',
                                                               '127.0.0.1',
                                                               '443') + '\n')
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_config_host_req_args_err(self):
        """Testing the configure server requires host arg."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'server', 'config']
            CLI().main()

    def test_config_host_alpha_port_err(self):
        """Testing the configure server requires bad port."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'server', 'config',
                        '--host', '127.0.0.1', '--port', 'abc']
            CLI().main()

    def test_success_config_server(self):
        """Testing the configure server green path."""
        config_out = StringIO()
        sys.argv = ['/bin/qpc', 'server', 'config',
                    '--host', '127.0.0.1', '--port', '8005']
        with redirect_stdout(config_out):
            CLI().main()
            config = read_server_config()
            self.assertEqual(config['host'], '127.0.0.1')
            self.assertEqual(config['port'], 8005)
            self.assertEqual(config_out.getvalue(),
                             messages.SERVER_CONFIG_SUCCESS % ('https',
                                                               '127.0.0.1',
                                                               '8005') + '\n')

    def test_config_server_default_port(self):
        """Testing the configure server default port."""
        sys.argv = ['/bin/qpc', 'server', 'config',
                    '--host', '127.0.0.1']
        CLI().main()
        config = read_server_config()
        self.assertEqual(config['host'], '127.0.0.1')
        self.assertEqual(config['port'], 443)

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_server_config({})

        sys.argv = ['/bin/qpc', 'server', 'config',
                    '--host', '127.0.0.1']
        CLI().main()
        config = read_server_config()
        self.assertEqual(config['host'], '127.0.0.1')
        self.assertEqual(config['port'], 443)

    def test_run_command_no_config(self):
        """Test running command without config."""
        write_server_config({})

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'cred']
            CLI().main()
