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
"""LoginHostCommand is used to login with username and password."""

from __future__ import print_function

from getpass import getpass

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.translation import _
from qpc.utils import delete_client_token, write_client_token

from requests import codes


# pylint: disable=too-few-public-methods
class LoginHostCommand(CliCommand):
    """Defines the login host command.

    This command is for logging into the target
    host for the CLI.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.LOGIN

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            server.LOGIN_URI, [codes.ok])

        self.parser.add_argument('--username', dest='username',
                                 metavar='USERNAME',
                                 help=_(messages.LOGIN_USER_HELP),
                                 required=False)
        self.username = None
        self.password = None

    def _validate_args(self):
        CliCommand._validate_args(self)

        delete_client_token()
        if 'username' in self.args and self.args.username:
            # check for file existence on system
            self.username = self.args.username
        else:
            self.username = input(_(messages.LOGIN_USERNAME_PROMPT))

        self.password = getpass()

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = {'username': self.username,
                            'password': self.password}

    def _handle_response_success(self):
        json_data = self.response.json()
        write_client_token(json_data)
        print(_(messages.LOGIN_SUCCESS))
