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
"""ScanPauseCommand is used to pause a specific system scan."""

from __future__ import print_function

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

from requests import codes


# pylint: disable=too-few-public-methods
class ScanPauseCommand(CliCommand):
    """Defines the pause command.

    This command is for pausing a specific scan to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.PAUSE

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
            self.req_path = self.req_path + str(self.args.id) + '/pause/'

    def _handle_response_success(self):
        print(_(messages.SCAN_PAUSED % self.args.id))
