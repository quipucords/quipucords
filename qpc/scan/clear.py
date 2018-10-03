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
"""ScanClearCommand is used to clear one or all host scans."""

from __future__ import print_function

import sys

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import DELETE, GET, request
from qpc.translation import _
from qpc.utils import handle_error_response

from requests import codes


# pylint: disable=too-few-public-methods
class ScanClearCommand(CliCommand):
    """Defines the clear command.

    This command is for clearing a specific scan or all scans.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.CLEAR

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            scan.SCAN_URI, [codes.ok])
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--name', dest='name', metavar='NAME',
                           help=_(messages.SCAN_NAME_HELP))
        group.add_argument('--all', dest='all', action='store_true',
                           help=_(messages.SCAN_CLEAR_ALL_HELP))

    def _build_req_params(self):
        if self.args.name:
            self.req_params = {'name': self.args.name}

    def _delete_entry(self, scan_entry, print_out=True):
        deleted = False
        delete_uri = scan.SCAN_URI + str(scan_entry['id']) + '/'
        response = request(DELETE, delete_uri, parser=self.parser)
        name = scan_entry['name']
        # pylint: disable=no-member
        if response.status_code == codes.no_content:
            deleted = True
            if print_out:
                print(_(messages.SCAN_REMOVED % name))
        else:
            handle_error_response(response)
            if print_out:
                print(_(messages.SCAN_FAILED_TO_REMOVE % name))
        return deleted

    # pylint: disable=too-many-branches
    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get('count', 0)
        results = json_data.get('results', [])
        if self.args.name and count == 0:
            print(_(messages.SCAN_NOT_FOUND % self.args.name))
            sys.exit(1)
        elif self.args.name and count == 1:
            # delete single scan
            entry = results[0]
            if self._delete_entry(entry) is False:
                sys.exit(1)
        elif self.args.name and count > 1:
            for result in results:
                if result['name'] == self.args.name:
                    if self._delete_entry(result) is False:
                        sys.exit(1)
        elif count == 0:
            print(_(messages.SCAN_NO_SCANS_TO_REMOVE))
            sys.exit(1)
        else:
            # remove all scan entries
            remove_error = []
            next_link = json_data.get('next')
            for entry in results:
                if self._delete_entry(entry, print_out=False) is False:
                    remove_error.append(entry['id'])
            if remove_error != []:
                scan_err = ','.join(str(remove_error))
                print(_(messages.SCAN_PARTIAL_REMOVE % scan_err))
                sys.exit(1)
            else:
                if not next_link:
                    print(messages.SCAN_CLEAR_ALL_SUCCESS)
                else:
                    self._do_command()
