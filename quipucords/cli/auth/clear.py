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
""" AuthClearCommand is used to clear specific credential
for system access or all credentials
"""

from __future__ import print_function
import sys
from requests import codes
from cli.utils import handle_error_response
from cli.clicommand import CliCommand
import cli.auth as auth
from cli.request import GET, DELETE, request


# pylint: disable=too-few-public-methods
class AuthClearCommand(CliCommand):
    """
    This command is for clearing a specific credential or all credentials.
    """
    SUBCOMMAND = auth.SUBCOMMAND
    ACTION = auth.CLEAR

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            auth.AUTH_URI, [codes.ok])
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--name', dest='name', metavar='NAME',
                           help='auth credential name')
        group.add_argument('--all', dest='all', action='store_true',
                           help='remove all credentials')

    def _build_req_params(self):
        if self.args.name:
            self.req_params = {'name': self.args.name}

    def _delete_entry(self, auth_entry, print_out=True):
        deleted = False
        delete_uri = auth.AUTH_URI + str(auth_entry['id']) + '/'
        response = request(DELETE, delete_uri, parser=self.parser)
        name = auth_entry['name']
        # pylint: disable=no-member
        if response.status_code == codes.no_content:
            deleted = True
            if print_out:
                print('Auth "%s" was removed' % name)
        else:
            handle_error_response(response)
            if print_out:
                print('Failed to remove credential "%s"' % name)
        return deleted

    def _handle_response_success(self):
        json_data = self.response.json()
        response_len = len(json_data)
        if self.args.name and response_len == 0:
            print('Auth "%s" was not found' % self.args.name)
            sys.exit(1)
        elif self.args.name and response_len == 1:
            # delete single credential
            entry = json_data[0]
            if self._delete_entry(entry) is False:
                sys.exit(1)
        elif response_len == 0:
            print("No credentials exist to be removed")
            sys.exit(1)
        else:
            # remove all entries
            remove_error = []
            for entry in json_data:
                if self._delete_entry(entry, print_out=False) is False:
                    remove_error.append(entry['name'])
            if remove_error != []:
                cred_err = ','.join(remove_error)
                print('Some credentials were removed, however an error'
                      ' occurred removing the following credentials: %s'
                      % cred_err)
                sys.exit(1)
            else:
                print('All credentials were removed')
