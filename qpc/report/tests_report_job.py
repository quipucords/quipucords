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
"""Test the CLI module."""

import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.report import JOB_URI
from qpc.report.job import ReportJobCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportJobTests(unittest.TestCase):
    """Class for testing the job commands for qpc."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        self.url = get_server_location() + JOB_URI

    def tearDown(self):
        """Remove test setup."""
        sys.stderr = self.orig_stderr

    def test_job_valid_id(self):
        """Test the job command with a vaild ID."""
        json = {'id': 1, 'scan_type': 'fingerprint',
                          'status': 'completed',
                          'status_message': 'Job is complete.',
                          'tasks': [{
                              'scan_type': 'fingerprint',
                              'status': 'completed',
                              'status_message': 'Task ran successfully',
                              'start_time': 'time',
                              'end_time': 'time'}],
                          'report_id': 10,
                          'start_time': 'time',
                          'end_time': 'time',
                          'systems_fingerprint_count': 0}
        report_out = StringIO()

        with requests_mock.Mocker() as mocker:
            print(self.url)
            mocker.get(self.url + '1/',
                       status_code=200,
                       json=self.good_json)
            nac = ReportJobCommand(SUBPARSER)
            args = Namespace(job_id='1')
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.JOB_ID_STATUS % ('1',
                                                           'Job is complete.',
                                                           '10'))

    def test_job_id_not_exist(self):
        """Test the job command with an invalid ID."""
        report_out = StringIO()
        with requests_mock.Mocker() as mocker:
            mocker.get(self.url + '1/', status_code=404, json=None)
            nac = ReportJobCommand(SUBPARSER)
            args = Namespace(job_id='1')
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(report_out.getvalue(),
                                     messages.JOB_ID_NOT_FOUND % '1')
