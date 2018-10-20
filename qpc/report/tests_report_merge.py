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

from qpc import messages
from qpc.report import ASYNC_MERGE_URI
from qpc.report.merge import ReportMergeCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

TMP_DETAILSFILE1 = ('/tmp/testdetailsreport1.json',
                    '{"id": 1,"sources":[{"facts": ["AB"],"server_id": "8"}]}')
TMP_DETAILSFILE2 = ('/tmp/testdetailsreport2.json',
                    '{"id": 2, \n "sources": [{"source_name": "source2"}]}')
TMP_NOTJSONFILE = ('/tmp/testnotjson.txt',
                   'not a json file')
TMP_BADDETAILS1 = ('/tmp/testbaddetailsreport_source.json',
                   '{"id": 4,"bsources":[{"facts": ["A"],"server_id": "8"}]}')
TMP_BADDETAILS2 = ('/tmp/testbadetailsreport_facts.json',
                   '{"id": 4,"sources":[{"bfacts": ["A"],"server_id": "8"}]}')
TMP_BADDETAILS3 = ('/tmp/testbaddetailsreport_server_id.json',
                   '{"id": 4,"sources":[{"facts": ["A"],"bserver_id": "8"}]}')
TMP_BADDETAILS4 = ('/tmp/testbaddetailsreport_bad_json.json',
                   '{"id":3,"sources"[this is bad]')
TMP_BADDETAILS5 = ('/tmp/testbaddetailsinvalidreporttype.json',
                   '{"report_type": "durham"}')
TMP_GOODDETAILS = ('/tmp/testgooddetailsreport.json',
                   '{"id": 4,"sources":[{"facts": ["A"],"server_id": "8"}]}')
NONEXIST_FILE = ('/tmp/does/not/exist/bad.json')
JSON_FILES_LIST = [TMP_DETAILSFILE1, TMP_DETAILSFILE2, TMP_NOTJSONFILE,
                   TMP_BADDETAILS1, TMP_BADDETAILS2, TMP_BADDETAILS3,
                   TMP_GOODDETAILS, TMP_BADDETAILS5]
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
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
            with open(file[0], 'w') as test_file:
                test_file.write(file[1])

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
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
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
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
                             report_ids=None,
                             json_dir=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(messages.REPORT_SUCCESSFULLY_MERGED %
                                 ('1', '1'), report_out.getvalue().strip())

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
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
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
                             report_ids=None,
                             json_dir=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)

    def test_detail_merge_report_ids(self):
        """Testing report merge command with report ids."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=201,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=None,
                             report_ids=[1, 2],
                             json_dir=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_MERGED % (
                                     '1', '1'))

    def test_detail_merge_error_report_ids(self):
        """Testing report merge error with report ids."""
        report_out = StringIO()

        error_message = 'fake_message'
        put_report_data = {'reports': [error_message]}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=400,
                       json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=None,
                             report_ids=[1, 2],
                             json_dir=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)

    def test_detail_merge_json_files(self):
        """Testing report merge command with json files."""
        report_out = StringIO()

        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201,
                        json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=[TMP_DETAILSFILE1[0],
                                         TMP_GOODDETAILS[0]],
                             report_ids=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_MERGED % ('1', '1'),
                              report_out.getvalue().strip())

    def test_detail_merge_json_files_not_exist(self):
        """Testing report merge file not found error with json files."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=[TMP_DETAILSFILE1[0],
                                     NONEXIST_FILE[0]],
                         report_ids=None,
                         json_dir=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.FILE_NOT_FOUND % NONEXIST_FILE[0],
                              report_out.getvalue().strip())

    def test_detail_merge_error_json_files(self):
        """Testing report merge error with json files."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=[TMP_DETAILSFILE1[0],
                                     TMP_NOTJSONFILE[0]],
                         report_ids=None,
                         json_dir=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_error_no_args(self):
        """Testing report merge error with no arguments."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None,
                         json_dir=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_error_too_few_args(self):
        """Testing report merge error with only 1 job id."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=[1],
                         json_files=None,
                         report_ids=None,
                         json_dir=None)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_json_directory(self):
        """Testing report merge command with json directory."""
        report_out = StringIO()
        put_report_data = {'id': 1}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201,
                        json=put_report_data)
            nac = ReportMergeCommand(SUBPARSER)
            args = Namespace(scan_job_ids=None,
                             json_files=None,
                             report_ids=None,
                             json_dir=['/tmp/'])
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_MERGED % ('1', '1'),
                              report_out.getvalue().strip())

    def test_detail_merge_json_directory_error_dir_not_found(self):
        """Testing report merge command with json_dir parameter (notdir)."""
        bad_json_directory = '/tmp/does/not/exist/1316'
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None,
                         json_dir=bad_json_directory)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_json_directory_error_path_passed(self):
        """Testing report merge command with json_dir parameter (file)."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None,
                         json_dir=TMP_BADDETAILS1[0])
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_json_invalid_report_type_passed(self):
        """Testing report merge command bad report_type."""
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None,
                         json_dir=TMP_BADDETAILS5[0])
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)

    def test_detail_merge_json_directory_no_detail_reports(self):
        """Testing report merge command with json_dir (no details)."""
        files_that_pass = [TMP_GOODDETAILS]
        for file in files_that_pass:
            if os.path.isfile(file[0]):
                os.remove(file[0])
        report_out = StringIO()
        nac = ReportMergeCommand(SUBPARSER)
        args = Namespace(scan_job_ids=None,
                         json_files=None,
                         report_ids=None,
                         json_dir='/tmp/')
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)
