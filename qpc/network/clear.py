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
""" NetworkClearCommand is used to clear specific network profile
 or all network profiles
"""

from __future__ import print_function
import sys
from requests import codes
from qpc.utils import handle_error_response
from qpc.clicommand import CliCommand
import qpc.network as network
from qpc.request import GET, DELETE, request


# pylint: disable=too-few-public-methods
class NetworkClearCommand(CliCommand):
    """
    This command is for clearing a specific network profile or all network
    profiles.
    """
    SUBCOMMAND = network.SUBCOMMAND
    ACTION = network.CLEAR

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            network.NETWORK_URI, [codes.ok])
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--name', dest='name', metavar='NAME',
                           help='profile name')
        group.add_argument('--all', dest='all', action='store_true',
                           help='remove all network profiles')

    def _build_req_params(self):
        if self.args.name:
            self.req_params = {'name': self.args.name}

    def _delete_entry(self, profile_entry, print_out=True):
        deleted = False
        delete_uri = network.NETWORK_URI + str(profile_entry['id']) + '/'
        response = request(DELETE, delete_uri, parser=self.parser)
        name = profile_entry['name']
        # pylint: disable=no-member
        if response.status_code == codes.no_content:
            deleted = True
            if print_out:
                print('Profile "%s" was removed' % name)
        else:
            handle_error_response(response)
            if print_out:
                print('Failed to remove profile "%s"' % name)
        return deleted

    def _handle_response_success(self):
        json_data = self.response.json()
        response_len = len(json_data)
        if self.args.name and response_len == 0:
            print('Profile "%s" was not found' % self.args.name)
            sys.exit(1)
        elif self.args.name and response_len == 1:
            # delete single credential
            entry = json_data[0]
            if self._delete_entry(entry) is False:
                sys.exit(1)
        elif response_len == 0:
            print("No profiles exist to be removed")
            sys.exit(1)
        else:
            # remove all entries
            remove_error = []
            for entry in json_data:
                if self._delete_entry(entry, print_out=False) is False:
                    remove_error.append(entry['name'])
            if remove_error != []:
                cred_err = ','.join(remove_error)
                print('Some profiles were removed, however an error'
                      ' occurred removing the following profiles: %s'
                      % cred_err)
                sys.exit(1)
            else:
                print('All profiles were removed')
