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
"""ScanCancelCommand is used to cancel a specific system scan."""

from __future__ import print_function

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

from requests import codes

# pylint: disable=too-few-public-methods


class ScanCancelCommand(CliCommand):
    """Defines the cancel command.

    This command is for cancel a specific scan to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.CANCEL

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PUT,
                            scan.SCAN_JOB_URI, [codes.ok])
        self.parser.add_argument('--id', dest='id', metavar='ID',
                                 help=_(messages.SCAN_JOB_ID_HELP),
                                 required=True)

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.id:
            self.req_path = self.req_path + str(self.args.id) + '/cancel/'

    def _handle_response_success(self):
        print(_(messages.SCAN_CANCELED % self.args.id))
