#!/usr/bin/env python
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
""" AuthAddCommand is used to add authentication credentials
for system access
"""

from __future__ import print_function
from requests import codes
from cli.request import POST
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.auth.utils import validate_sshkeyfile, build_credential_payload


# pylint: disable=too-few-public-methods
class AuthAddCommand(CliCommand):
    """
    This command is for creating new auths which can be later associated with
    profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.ADD

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            auth.AUTH_URI, [codes.created])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='auth credential name', required=True)
        self.parser.add_argument('--username', dest='username',
                                 metavar='USERNAME',
                                 help='user name for authenticating'
                                      ' against target system', required=True)
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--password', dest='password',
                           action='store_true',
                           help='password for authenticating against'
                                ' target system')
        group.add_argument('--sshkeyfile', dest='filename',
                           metavar='FILENAME',
                           help='file containing SSH key')
        self.parser.add_argument('--sudo-password', dest='sudo_password',
                                 action='store_true',
                                 help='password for running sudo')

    def _validate_args(self):
        CliCommand._validate_args(self)

        if self.args.filename:
            # check for file existence on system
            self.args.filename = validate_sshkeyfile(self.args.filename,
                                                     self.parser)

    def _build_data(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionary representing the auth being added
        """
        self.req_payload = build_credential_payload(self.args)

    def _handle_response_success(self):
        print('Auth "%s" was added' % self.args.name)
