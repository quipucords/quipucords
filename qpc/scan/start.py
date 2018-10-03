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
"""ScanStartCommand is used to trigger a host scan."""

from __future__ import print_function

import sys

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.scan.utils import get_scan_object_id
from qpc.translation import _

from requests import codes


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
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.SCAN_NAME_HELP),
                                 required=True)

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.name:
            # check for existence of scan object
            found, scan_object_id = get_scan_object_id(self.parser,
                                                       self.args.name)
            if found is False:
                sys.exit(1)
            else:
                self.req_path = scan.SCAN_URI + scan_object_id + 'jobs/'

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_STARTED % json_data.get('id')))
