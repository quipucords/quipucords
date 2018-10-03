#!/usr/bin/env python
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
"""CredClearCommand is used to clear a or all credentials."""

from __future__ import print_function

import sys

import qpc.cred as credential
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import DELETE, GET, request
from qpc.translation import _
from qpc.utils import handle_error_response

from requests import codes


# pylint: disable=too-few-public-methods
class CredClearCommand(CliCommand):
    """Defines the clear command.

    This command is for clearing a specific credential or all credentials.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.CLEAR

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            credential.CREDENTIAL_URI, [codes.ok])
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--name', dest='name', metavar='NAME',
                           help=_(messages.CRED_NAME_HELP))
        group.add_argument('--all', dest='all', action='store_true',
                           help=_(messages.CRED_CLEAR_ALL_HELP))

    def _build_req_params(self):
        if self.args.name:
            self.req_params = {'name': self.args.name}

    def _delete_entry(self, credential_entry, print_out=True):
        deleted = False
        delete_uri = credential.CREDENTIAL_URI + \
            str(credential_entry['id']) + '/'
        response = request(DELETE, delete_uri, parser=self.parser)
        name = credential_entry['name']
        # pylint: disable=no-member
        if response.status_code == codes.no_content:
            deleted = True
            if print_out:
                print(_(messages.CRED_REMOVED % name))
        else:
            handle_error_response(response)
            if print_out:
                print(_(messages.CRED_FAILED_TO_REMOVE % name))
        return deleted

    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get('count', 0)
        if self.args.name and count == 0:
            print(_(messages.CRED_NOT_FOUND % self.args.name))
            sys.exit(1)
        elif self.args.name and count == 1:
            # delete single credential
            entry = json_data.get('results')[0]
            if self._delete_entry(entry) is False:
                sys.exit(1)
        elif count == 0:
            print(_(messages.CRED_NO_CREDS_TO_REMOVE))
            sys.exit(1)
        else:
            # remove all entries
            remove_error = []
            next_link = json_data.get('next')
            results = json_data.get('results')
            for entry in results:
                if self._delete_entry(entry, print_out=False) is False:
                    remove_error.append(entry['name'])
            if remove_error != []:
                cred_err = ','.join(remove_error)
                print(_(messages.CRED_PARTIAL_REMOVE % cred_err))
                sys.exit(1)
            else:
                if not next_link:
                    print(_(messages.CRED_CLEAR_ALL_SUCCESS))
                else:
                    self._do_command()
