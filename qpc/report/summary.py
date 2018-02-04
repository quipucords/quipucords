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
"""ReportSummaryCommand is used to show summary report information."""

from __future__ import print_function
import sys
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
from qpc.request import request, GET
import qpc.report as report
import qpc.scan as scan
from qpc.translation import _
import qpc.messages as messages
from qpc.utils import (validate_write_file,
                       write_file)


# pylint: disable=too-few-public-methods
class ReportSummaryCommand(CliCommand):
    """Defines the show command.

    This command is for showing the summary report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.SUMMARY
    SUMMARY_URI = report.REPORT_URI

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            self.SUMMARY_URI, [codes.ok])
        self.parser.add_argument('--id', dest='scan_id', metavar='SCAN_ID',
                                 help=_(messages.REPORT_SUMMARY_ID_HELP),
                                 required=True)

        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--json', dest='output_json', action='store_true',
                           help=_(messages.REPORT_SUMMARY_OUTPUT_JSON_HELP))
        group.add_argument('--csv', dest='output_csv', action='store_true',
                           help=_(messages.REPORT_SUMMARY_OUTPUT_CSV_HELP))

        self.parser.add_argument('--output-file', dest='path', metavar='PATH',
                                 help=_(messages.REPORT_SUMMARY_PATH_HELP),
                                 required=True)
        self.fact_collection_id = None

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.output_json:
            self.req_headers = {'Accept': 'application/json'}
        if self.args.output_csv:
            self.req_headers = {'Accept': 'text/csv'}

        try:
            validate_write_file(self.args.path, 'output-file')
        except ValueError as error:
            print(error)
            sys.exit(1)

        # Lookup scan job id
        response = request(parser=self.parser, method=GET,
                           path='%s%s' % (scan.SCAN_URI, self.args.scan_id),
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            self.fact_collection_id = json_data.get('fact_collection_id')
            if self.fact_collection_id:
                self.req_path = '%s?fact_collection_id=%s' % (
                    self.req_path, self.fact_collection_id)
            else:
                print(_(messages.REPORT_SUMMARY_NO_REPORT_FOR_SJ %
                        self.args.scan_id))
                sys.exit(1)
        else:
            print(_(messages.REPORT_SUMMARY_SJ_DOES_NOT_EXIST %
                    self.args.scan_id))
            sys.exit(1)

    def _handle_response_success(self):
        file_content = None
        if self.args.output_json:
            file_content = self.response.json()
            file_content = pretty_print(file_content)
        else:
            file_content = self.response.text
            print()
        write_file(self.args.path, file_content)

    def _handle_response_error(self):
        print(_(messages.REPORT_SUMMARY_NO_REPORT_FOR_SJ %
                self.args.scan_id))
        sys.exit(1)
