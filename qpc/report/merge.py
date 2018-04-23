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

import json
import os
import sys

import qpc.messages as messages
import qpc.report as report
from qpc.clicommand import CliCommand
from qpc.request import GET, POST, PUT, request
from qpc.scan import SCAN_JOB_URI
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
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--job-ids', dest='scan_job_ids', nargs='+',
                           metavar='SCAN_JOB_IDS', default=[],
                           help=_(messages.REPORT_SCAN_JOB_IDS_HELP))
        group.add_argument('--report-ids', dest='report_ids', nargs='+',
                           metavar='REPORT_IDS', default=[],
                           help=_(messages.REPORT_REPORT_IDS_HELP))
        group.add_argument('--json-files', dest='json_files', nargs='+',
                           metavar='JSON_FILES', default=[],
                           help=_(messages.REPORT_JSON_FILE_HELP))
        self.json = None
        self.report_ids = None

    @staticmethod
    def get_id_and_sources(filename):
        """Return the sources and id from a valid json details report file.

        :param filename: the filename to read
        :returns: the id and list of sources found
        :raises: ValueError if incoming value is not a file that could be found
        """
        input_path = os.path.expanduser(os.path.expandvars(filename))
        if os.path.isfile(input_path):
            try:
                with open(input_path, 'r') as in_file:
                    result = in_file.read()
                    report_id = json.loads(result).get('id')
                    sources = json.loads(result).get('sources')
                    if not report_id or not sources:
                        print(_(messages.REPORT_INVALID_JSON_FILE % filename))
                        sys.exit(1)
            except EnvironmentError as err:
                err_msg = (messages.READ_FILE_ERROR % (input_path, err))
                print(err_msg)
                sys.exit(1)
            return report_id, sources
        else:
            raise ValueError(_(messages.NOT_A_FILE % input_path))

    def _get_report_ids(self):
        """Grab the report ids from the scan job if it exists.

        :returns Boolean regarding the existence of scan jobs &
        the report ids
        """
        not_found = False
        report_ids = []
        for scan_job_id in set(self.args.scan_job_ids):
            # check for existence of scan_job
            path = SCAN_JOB_URI + str(scan_job_id) + '/'
            response = request(parser=self.parser, method=GET,
                               path=path,
                               params=None,
                               payload=None)
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                report_id = json_data.get('report_id', None)
                if report_id:
                    report_ids.append(report_id)
                else:
                    # there is not a report id associated with this scan job
                    print(_(messages.SCAN_JOB_REPORT_ID_DOES_NOT_EXIST %
                            scan_job_id))
                    not_found = True
            else:
                print(_(messages.SCAN_JOB_DOES_NOT_EXIST % scan_job_id))
                not_found = True
        return not_found, report_ids

    def _merge_json(self):
        """Combine the sources for each json file provided.

        :returns Json containing the sources of each file.
        """
        report_id = None
        all_sources = []
        if len(self.args.json_files) > 1:
            for file in self.args.json_files:
                try:
                    report_id, sources = self.get_id_and_sources(file)
                    all_sources += sources
                except ValueError:
                    print(_(messages.REPORT_INVALID_JSON_FILE % file))
                    sys.exit(1)
            self.json = {'id': report_id,
                         'sources': all_sources}
        else:
            print(_(messages.REPORT_JSON_FILES_HELP))
            sys.exit(1)

    def _validate_args(self):
        CliCommand._validate_args(self)
        report_ids = []
        if self.args.scan_job_ids:
            # check for existence of jobs & get report ids
            not_found, report_ids = self._get_report_ids()
            if not_found is True:
                sys.exit(1)
        elif self.args.report_ids:
            report_ids = self.args.report_ids
        elif self.args.json_files:
            self._merge_json()
        self.report_ids = report_ids

    def _build_data(self):
        """Construct the payload for a merging reports.

        :returns: a dictionary representing the jobs to merge
        """
        if self.args.json_files:
            self.req_path = report.JSON_FILE_MERGE_URI
            self.req_method = POST
            self.req_payload = self.json
        else:
            self.req_payload = {
                'reports': self.report_ids,
            }

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.REPORT_SUCCESSFULLY_MERGED % json_data['id']))

    def _handle_response_error(self):
        json_data = self.response.json()
        print(json_data['reports'][0])
        sys.exit(1)
