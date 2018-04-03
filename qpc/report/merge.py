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
"""ReportMergeCommand is used to merge scan jobs results."""

from __future__ import print_function

import sys

import qpc.messages as messages
import qpc.report as report
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

from requests import codes


# pylint: disable=too-few-public-methods
class ReportMergeCommand(CliCommand):
    """Defines the report merge command.

    This command is for merging scan job results into a
    single report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.MERGE

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PUT,
                            report.MERGE_URI, [codes.created])
        self.parser.add_argument('--ids', dest='scan_job_ids', nargs='+',
                                 metavar='SCAN_JOB_IDS', default=[],
                                 help=_(messages.REPORT_SCAN_JOB_IDS_HELP),
                                 required=True)

    def _build_data(self):
        """Construct the payload for a merging scan job results.

        :returns: a dictionary representing the jobs to merge
        """
        self.req_payload = {
            'jobs': self.args.scan_job_ids,
        }

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.REPORT_SUCCESSFULLY_MERGED % json_data['id']))

    def _handle_response_error(self):
        json_data = self.response.json()
        print(json_data['jobs'][0])
        sys.exit(1)
