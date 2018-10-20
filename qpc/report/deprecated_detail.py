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
"""DeprecatedReportDetailCommand is used to show detail report information."""

from __future__ import print_function

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.report.details import ReportDetailsCommand
from qpc.request import GET
from qpc.translation import _

from requests import codes

#############################################
# DEPRECATED: new function should not go here
#############################################


# pylint: disable=too-few-public-methods
class DeprecatedReportDetailCommand(ReportDetailsCommand):
    """Defines the report details command.

    This command is for showing the details report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.DETAIL

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member,non-parent-init-called
        # pylint: disable=super-init-not-called
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            report.REPORT_URI, [codes.ok])
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument('--scan-job', dest='scan_job_id',
                              metavar='SCAN_JOB_ID',
                              help=_(messages.REPORT_SCAN_JOB_ID_HELP))
        id_group.add_argument('--report', dest='report_id',
                              metavar='REPORT_ID',
                              help=_(messages.REPORT_REPORT_ID_HELP))

        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--json', dest='output_json', action='store_true',
                           help=_(messages.REPORT_OUTPUT_JSON_HELP))
        group.add_argument('--csv', dest='output_csv', action='store_true',
                           help=_(messages.REPORT_OUTPUT_CSV_HELP))

        self.parser.add_argument('--output-file', dest='path', metavar='PATH',
                                 help=_(messages.REPORT_PATH_HELP),
                                 required=True)
        self.report_id = None

    def _validate_args(self):
        print(_(messages.REPORT_DETAIL_DEPRECATED))
        super()._validate_args()
