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
"""ScanShowCommand is used to show info on a specific system scan."""

from __future__ import print_function
import sys
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
import qpc.scan as scan
from qpc.request import GET, request
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class ScanShowCommand(CliCommand):
    """Defines the show command.

    This command is for showing the status of a specific scan
    to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.SHOW

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            scan.SCAN_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SCAN_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--id', dest='id', metavar='ID',
                                 help=_(messages.SCAN_ID_HELP), required=False)
        self.parser.add_argument('--results', dest='results',
                                 action='store_true',
                                 help=_(messages.SCAN_RESULTS_HELP),
                                 required=False)

    def _get_scan_id(self):
        not_found = False
        scan_id = []
        response = request(parser=self.parser, method=GET,
                               path=scan.SCAN_URI,
                               params={'name': self.args.name},
                               payload=None)
        if response.status.code == codes.ok:
            json_data = response.json()
            count = json_data.get('count', 0)
            result = json_data.get('results', [])
            if count == 1:
                scan_entry = result[0]
                scan_id.append(scan_entry['id'])
            else:
                print(_(messages.SCAN_DOES_NOT_EXIST % self.args.name))
                not_found = True
        else:
            print(_(messages.SCAN_DOES_NOT_EXIST % self.args.name))
            not_found = True
        return not_found, scan_id

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.name:
            response = self._get_scan_id()
            if response[0]:
                self.args.id = response[1][0]
                self.req_path = self.req_path + str(self.args.id) + '/'
            else:
                sys.exit(1)
        if self.args.results:
            self.req_path += 'results/'

    def _handle_response_success(self):
        json_data = self.response.json()
        data = pretty_print(json_data)
        print(data)

    def _handle_response_error(self):
        print(_(messages.SCAN_DOES_NOT_EXIST % self.args.name))
        sys.exit(1)
