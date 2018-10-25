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
"""ReportMergeStatusCommand is used to show job merge information."""

from __future__ import print_function

import sys

import qpc.report as report
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _

from requests import codes


# pylint: disable=too-few-public-methods
class ReportMergeStatusCommand(CliCommand):
    """Defines the job command.

    This command is for checking the job status of a merge command.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.MERGE_STATUS

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            report.ASYNC_MERGE_URI, [codes.ok])
        self.parser.add_argument('--job', dest='job_id', metavar='JOB_ID',
                                 help=_(messages.REPORT_JOB_ID_HELP),
                                 required=True)

    def _build_req_params(self):
        self.req_path = report.ASYNC_MERGE_URI + str(self.args.job_id) + '/'

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.MERGE_JOB_ID_STATUS % (
            self.args.job_id,
            json_data.get('status').lower())))
        if json_data.get('report_id'):
            print(_(messages.DISPLAY_REPORT_ID % (json_data.get('report_id'),
                                                  json_data.get('report_id'))))

    def _handle_response_error(self):
        print(_(messages.MERGE_JOB_ID_NOT_FOUND % self.args.job_id))
        sys.exit(1)
