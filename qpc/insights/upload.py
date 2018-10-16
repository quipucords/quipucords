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
"""Upload is used to upload files through the insights client."""

from __future__ import print_function

import subprocess
import sys
import tarfile

import qpc.insights as insights
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.insights.utils import (check_insights_install,
                                check_successful_upload,
                                insights_command,
                                test_insights_command)
from qpc.request import GET
from qpc.translation import _

# pylint:disable=no-member
from requests import codes


# pylint: disable=too-few-public-methods
class InsightsUploadCommand(CliCommand):
    """Defines the Insights command.

    This command is for uploading QPC reports throught the insights client.
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.UPLOAD

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            insights.REPORT_URI, [codes.ok])
        self.parser.add_argument('--report', dest='report_id',
                                 required=True)
        self.parser.add_argument('--test', dest='test', action='store_true')
        self.tmp_file_name = '/tmp/insights_upload.json'
        self.tmp_tar_name = '/tmp/test.tar.gz'
        self.insights_command = None

    def _validate_args(self):
        CliCommand._validate_args(self)
        self.req_headers = {'Accept': 'application/json'}
        if self.args.test:
            self.insights_command = \
                test_insights_command(self.tmp_tar_name,
                                      insights.CONTENT_TYPE)
        else:
            self.insights_command = insights_command(self.tmp_tar_name,
                                                     insights.CONTENT_TYPE)
        connection_test_command = self.insights_command[:-2]
        connection_test_command.append('--test-connection')
        proc = subprocess.Popen(connection_test_command,
                                stderr=subprocess.PIPE)
        format_streamdata = proc.communicate()[1].decode('utf-8').strip('\n')
        code = proc.returncode
        print(_(messages.CHECKING_INSIGHTS %
                (' '.join(connection_test_command))))
        insights_check = check_insights_install(format_streamdata)
        print(format_streamdata)
        print(code)
        if not insights_check or code is not 0:
            print(_(messages.BAD_INSIGHTS_CHECK %
                    (format_streamdata)))
            sys.exit(1)
        else:
            print(_(messages.GOOD_INSIGHTS_CHECK))

    def _build_req_params(self):
        self.req_path = \
            insights.REPORT_URI + str(self.args.report_id) + '/deployments/'

    def _handle_response_success(self):
        tar = tarfile.open(self.tmp_tar_name, 'w:gz')
        with open(self.tmp_file_name, 'w+') as file:
            for chunk in self.response.iter_content(chunk_size=128):
                file.write(str(chunk))
        tar.add(self.tmp_file_name)
        tar.close()
        print(_(messages.UPLOADING_REPORT_INSIGHTS %
                (' '.join(self.insights_command))))
        proc = subprocess.Popen(self.insights_command, stderr=subprocess.PIPE)
        format_streamdata = proc.communicate()[1].decode('utf-8').strip('\n')
        code = proc.returncode
        report_check = check_successful_upload(format_streamdata)
        if not report_check or code is not 0:
            print(_(messages.BAD_INSIGHTS_UPLOAD %
                    (format_streamdata)))
        else:
            print(_(messages.GOOD_INSIGHTS_UPLOAD %
                    (format_streamdata)))
            sys.exit(1)

    def _handle_response_error(self):
        print(_(messages.INSIGHTS_REPORT_NOT_FOUND % (self.args.report_id)))
        sys.exit(1)
