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
"""ScanListCommand is used to list system scans."""

from __future__ import print_function
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
import qpc.scan as scan
from qpc.request import GET
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class ScanListCommand(CliCommand):
    """Defines the list command.

    This command is for listing sources scans used to gather system facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.LIST

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            scan.SCAN_URI, [codes.ok])
        self.parser.add_argument('--type', dest='type',
                                 choices=[scan.SCAN_TYPE_CONNECT,
                                          scan.SCAN_TYPE_INSPECT],
                                 metavar='TYPE',
                                 help=_(messages.SCAN_TYPE_FILTER_HELP),
                                 required=False)
        self.parser.add_argument('--status', dest='status',
                                 choices=[scan.SCAN_STATUS_CREATED,
                                          scan.SCAN_STATUS_PENDING,
                                          scan.SCAN_STATUS_RUNNING,
                                          scan.SCAN_STATUS_PAUSED,
                                          scan.SCAN_STATUS_CANCELED,
                                          scan.SCAN_STATUS_COMPLETED,
                                          scan.SCAN_STATUS_FAILED],
                                 metavar='STATUS',
                                 help=_(messages.SCAN_STATUS_FILTER_HELP),
                                 required=False)

    def _build_req_params(self):
        """Add filter by scan_type/state query param."""
        if 'type' in self.args and self.args.type:
            self.req_params = {'scan_type': self.args.type}
        if 'status' in self.args and self.args.status:
            self.req_params = {'status': self.args.status}

    def _handle_response_success(self):
        json_data = self.response.json()
        if json_data == []:
            print(_(messages.SCAN_LIST_NO_SCANS))
        else:
            data = pretty_print(json_data)
            print(data)
