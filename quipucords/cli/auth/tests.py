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

import contextlib
import unittest
import sys
import six
from cli.cli import CLI


# pylint: disable=too-few-public-methods
class HushUpStderr(object):
    """Class used to quiet standard error output"""
    def write(self, stream):
        """Ignore standard error output"""
        pass


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream"""

    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


class AuthCliTests(unittest.TestCase):
    """Class for testing the auth cli commands for qpc"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_add_auth(self):
        """Testing the add auth command"""
        auth_out = six.StringIO()
        with redirect_stdout(auth_out):
            sys.argv = ['/bin/qpc', 'auth', 'add', '--name', 'auth1']
            CLI().main()
            self.assertEqual(auth_out.getvalue(),
                             'Auth "auth1" was added\n')
