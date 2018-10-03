#!/usr/bin/env python
#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""LogoutHostCommand is used to remove any existing login token."""

from __future__ import print_function

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _
from qpc.utils import delete_client_token

from requests import codes


# pylint: disable=too-few-public-methods
class LogoutHostCommand(CliCommand):
    """Defines the logout host command.

    This command is for logging out of theserver for the CLI.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.LOGOUT

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PUT,
                            server.LOGOUT_URI, [codes.ok])

    def _handle_response_success(self):
        """Remove the client token."""
        delete_client_token()
        print(_(messages.LOGOUT_SUCCESS))
