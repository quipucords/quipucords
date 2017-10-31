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
""" ScanShowCommand is used to show info on a specific system scan
"""

from __future__ import print_function
import sys
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
import qpc.scan as scan
from qpc.request import GET
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class ScanShowCommand(CliCommand):
    """
    This command is for showing the status of a specific scan
    to gather facts.
    """
    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.SHOW

    def __init__(self, subparsers):
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            scan.SCAN_URI, [codes.ok])
        self.parser.add_argument('--id', dest='id', metavar='ID',
                                 help=_(messages.SCAN_ID_HELP), required=True)

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.id:
            self.req_path = self.req_path + str(self.args.id) + '/'

    def _handle_response_success(self):
        json_data = self.response.json()
        data = pretty_print(json_data)
        print(data)

    def _handle_response_error(self):
        print(_(messages.SCAN_DOES_NOT_EXIST % self.args.id))
        sys.exit(1)
