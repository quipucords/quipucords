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
"""SourceListCommand is used to list sources for system scans."""

from __future__ import print_function
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
import qpc.source as source
from qpc.request import GET
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class SourceListCommand(CliCommand):
    """Defines the list command.

    This command is for listing sources which can be later be used with a scan
    to gather facts.
    """

    SUBCOMMAND = source.SUBCOMMAND
    ACTION = source.LIST

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            source.SOURCE_URI, [codes.ok])
        self.parser.add_argument('--type', dest='type',
                                 choices=[source.NETWORK_SOURCE_TYPE,
                                          source.VCENTER_SOURCE_TYPE,
                                          source.SATELLITE_SOURCE_TYPE],
                                 metavar='TYPE',
                                 help=_(messages.SOURCE_TYPE_FILTER_HELP),
                                 required=False)

    def _build_req_params(self):
        """Add filter by source_type query param."""
        if 'type' in self.args and self.args.type:
            self.req_params = {'source_type': self.args.type}

    def _handle_response_success(self):
        json_data = self.response.json()
        if json_data == []:
            print(_(messages.SOURCE_LIST_NO_SOURCES))
        else:
            data = pretty_print(json_data)
            print(data)
