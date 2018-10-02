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
"""ReportDetailCommand is used to show detail report information."""

from __future__ import print_function

import sys

import qpc.messages as messages
import qpc.report as report
import qpc.scan as scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import (pretty_print,
                       validate_write_file,
                       write_file)

from requests import codes

class ReportJobCommand(CliCommand):
    """Defines the job command.

    This command is for checking the job status of a merge command.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.JOB

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            report.REPORT_URI, [codes.ok])
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument('--id', dest='job_id',
                              metavar='JOB_ID',
                              help=_(messages.REPORT_JOB_HELP))
        self.report_id = None

    def _validate_args(self):
        #TODO: This needs to be done.

    def _handle_response_success(self):
        #TODO: Figure out what needs to be returned from the backend.

    def _handle_response_error(self):
        #TODO: Figure out what nees to be returned from the backend.
