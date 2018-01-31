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
"""Test utilities for the CLI module."""

import contextlib
import sys


DEFAULT_CONFIG = {'host': '127.0.0.1', 'port': 8000, 'use_http': True}


# pylint: disable=too-few-public-methods
class HushUpStderr(object):
    """Class used to quiet standard error output."""

    def write(self, stream):
        """Ignore standard error output."""
        pass


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream."""
    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout
