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
"""ScanStartCommand is used to trigger a host scan."""

from __future__ import print_function
import sys
from requests import codes
from qpc.request import POST, GET, request
from qpc.clicommand import CliCommand
import qpc.source as source
import qpc.scan as scan
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class ScanStartCommand(CliCommand):
    """Defines the start command.

    This command is for triggering host scans with a source to gather system
    facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.START

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            scan.SCAN_URI, [codes.created])
        self.parser.add_argument('--source', dest='source',
                                 metavar='source',
                                 help=_(messages.SOURCE_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--max-concurrency', dest='max_concurrency',
                                 metavar='MAX_CONCURRENCY',
                                 type=int, default=50,
                                 help=_(messages.SCAN_MAX_CONCURRENCY_HELP))
        self.source_id = None

    def _validate_args(self):
        CliCommand._validate_args(self)

        # check for existence of source
        response = request(parser=self.parser, method=GET,
                           path=source.SOURCE_URI,
                           params={'name': self.args.source},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            if len(json_data) == 1:
                source_entry = json_data[0]
                self.source_id = source_entry['id']
            else:
                print(_(messages.SOURCE_DOES_NOT_EXIST % self.args.source))
                sys.exit(1)
        else:
            print(_(messages.SOURCE_DOES_NOT_EXIST % self.args.source))
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionary representing the auth being added
        """
        self.req_payload = {
            'source': self.source_id,
            'scan_type': scan.SCAN_TYPE_HOST,
            'max_concurrency': self.args.max_concurrency
        }

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_STARTED % json_data['id']))
