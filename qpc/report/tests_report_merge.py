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

import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

import qpc.messages as messages
from qpc.report import MERGE_URI
from qpc.report.merge import ReportMergeCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportDetailTests(unittest.TestCase):
    """Class for testing the scan show commands for qpc."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        self.test_json_filename = 'test_%d.json' % time.time()
        self.test_csv_filename = 'test_%d.csv' % time.time()
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_json_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.test_csv_filename)
        except FileNotFoundError:
            pass

    def test_detail_merge(self):
        """Testing report merge command."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=201,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=[1, 2])
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_MERGED % '1')

    def test_detail_merge_error(self):
        """Testing report merge error."""
        report_out = StringIO()

        error_message = 'fake_message'
        put_report_data = {'jobs': [error_message]}
        put_merge_url = get_server_location() + MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=400,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=[1, 2])
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(report_out.getvalue().strip(),
                                     error_message)
