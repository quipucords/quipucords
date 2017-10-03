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
""" AuthEditCommand is used to edit existing authentication credentials
for system access
"""

from __future__ import print_function
import sys
from requests import codes
from qpc.request import PATCH, GET, request
from qpc.clicommand import CliCommand
import qpc.auth as auth
from qpc.auth.utils import validate_sshkeyfile, build_credential_payload


# pylint: disable=too-few-public-methods
class AuthEditCommand(CliCommand):
    """
    This command is for editing existing auths which can be later associated
    with profiles to gather facts.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.EDIT

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PATCH,
                            auth.AUTH_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help='auth credential name', required=True)
        self.parser.add_argument('--username', dest='username',
                                 metavar='USERNAME',
                                 help='user name for authenticating'
                                      ' against target system', required=False)
        group = self.parser.add_mutually_exclusive_group(required=False)
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

        if not(self.args.username or self.args.password or
               self.args.sudo_password or self.args.filename):
            print('No arguments provided to edit credential %s' %
                  (self.args.name))
            self.parser.print_help()
            sys.exit(1)

        if self.args.filename:
            # check for file existence on system
            self.args.filename = validate_sshkeyfile(self.args.filename,
                                                     self.parser)

        # check for existence of credential
        response = request(parser=self.parser, method=GET, path=auth.AUTH_URI,
                           params={'name': self.args.name},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            if len(json_data) == 1:
                cred_entry = json_data[0]
                self.req_path = self.req_path + str(cred_entry['id']) + '/'
            else:
                print('Auth "%s" does not exist' % self.args.name)
                sys.exit(1)
        else:
            print('Auth "%s" does not exist' % self.args.name)
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionary representing the auth being added
        """
        self.req_payload = build_credential_payload(self.args, add_none=False)

    def _handle_response_success(self):
        print('Auth "%s" was updated' % self.args.name)
