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
from qpc.report import JSON_FILE_MERGE_URI, MERGE_URI
from qpc.report.merge import ReportMergeCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

TMP_DETAILSFILE1 = '/tmp/testdetailsreport1.JSON'
TMP_DETAILSFILE2 = '/tmp/testdetailsreport2.JSON'
TMP_NOTJSONFILE = '/tmp/testnotjson'
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
        if os.path.isfile(TMP_DETAILSFILE1):
            os.remove(TMP_DETAILSFILE1)
        with open(TMP_DETAILSFILE1, 'w') as test_details1:
            test_details1.write('{"id": 1, '
                                '"sources": [{"source_name": "source1"}]}')
        if os.path.isfile(TMP_DETAILSFILE2):
            os.remove(TMP_DETAILSFILE2)
        with open(TMP_DETAILSFILE2, 'w') as test_details2:
            test_details2.write('{"id": 1, '
                                '"sources": [{"source_name": "source2"}]}')
        if os.path.isfile(TMP_NOTJSONFILE):
            os.remove(TMP_NOTJSONFILE)
        with open(TMP_NOTJSONFILE, 'w') as test_notjson:
            test_notjson.write('Not a json file.')

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        if os.path.isfile(TMP_DETAILSFILE1):
            os.remove(TMP_DETAILSFILE1)
        if os.path.isfile(TMP_DETAILSFILE2):
            os.remove(TMP_DETAILSFILE2)
        if os.path.isfile(TMP_NOTJSONFILE):
            os.remove(TMP_NOTJSONFILE)
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_json_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.test_csv_filename)
        except FileNotFoundError:
            pass

    def test_detail_merge_job_ids(self):
        """Testing report merge command with scan job ids."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + MERGE_URI
        scanjob1_data = {'report_id': 1}
        scanjob2_data = {'report_id': 2}
        get_scanjob1_url = \
            get_server_location() + SCAN_JOB_URI + '1/'
        get_scanjob2_url = \
            get_server_location() + SCAN_JOB_URI + '2/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob1_url, status_code=200,
                       json=scanjob1_data)
            mocker.get(get_scanjob2_url, status_code=200,
                       json=scanjob2_data)
            mocker.put(put_merge_url, status_code=201,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=[1, 2],
                             json_files=None,
                             report_ids=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_MERGED % '1')

    def test_detail_merge_error_job_ids(self):
        """Testing report merge error with scan job ids."""
        report_out = StringIO()

        error_message = 'fake_message'
        scanjob1_data = {'report_id': 1}
        scanjob2_data = {'report_id': 2}
        put_report_data = {'reports': [error_message]}
        get_scanjob1_url = \
            get_server_location() + SCAN_JOB_URI + '1/'
        get_scanjob2_url = \
            get_server_location() + SCAN_JOB_URI + '2/'
        put_merge_url = get_server_location() + MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob1_url, status_code=200,
                       json=scanjob1_data)
            mocker.get(get_scanjob2_url, status_code=200,
                       json=scanjob2_data)
            mocker.put(put_merge_url, status_code=400,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=[1, 2],
                             json_files=None,
                             report_ids=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)

    def test_detail_merge_report_ids(self):
        """Testing report merge command with report ids."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=201,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=None,
                             report_ids=[1, 2])
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_MERGED % '1')

    def test_detail_merge_error_report_ids(self):
        """Testing report merge error with report ids."""
        report_out = StringIO()

        error_message = 'fake_message'
        put_report_data = {'reports': [error_message]}
        put_merge_url = get_server_location() + MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=400,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=None,
                             report_ids=[1, 2])
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)

    def test_detail_merge_json_files(self):
        """Testing report merge command with json files."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + JSON_FILE_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201,
                        json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=[TMP_DETAILSFILE1,
                                         TMP_DETAILSFILE1],
                             report_ids=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_MERGED % '1')

    def test_detail_merge_error_json_files(self):
        """Testing report merge error with json files."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=[TMP_DETAILSFILE1,
                                     TMP_NOTJSONFILE],
                         report_ids=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_error_no_args(self):
        """Testing report merge error with no arguments."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_error_too_few_args(self):
        """Testing report merge error with only 1 job id."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=[1],
                         json_files=None,
                         report_ids=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)
