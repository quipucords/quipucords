#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the CLI module."""

import unittest
import os
import sys
import time
import json
from io import StringIO
from argparse import ArgumentParser, Namespace
import requests_mock
from qpc.cli import CLI
from qpc.tests_utilities import HushUpStderr, redirect_stdout, DEFAULT_CONFIG
from qpc.report import REPORT_URI
from qpc.report.summary import ReportSummaryCommand
from qpc.utils import get_server_location, write_server_config
import qpc.messages as messages

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportSummaryTests(unittest.TestCase):
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

    def test_summary_report_as_json(self):
        """Testing retreiving summary report as json."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '?fact_collection_id=1'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       json=get_report_json_data)
            nac = ReportSummaryCommand(SUBPARSER)
            args = Namespace(id='1', output_json=True, output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.FILE_SUCCESSFULLY_WRITTEN %
                                 self.test_json_filename)
                with open(self.test_json_filename, 'r') as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_json_data, file_content_dict)

    def test_summary_report_as_csv(self):
        """Testing retreiving summary report as csv."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '?fact_collection_id=1'
        get_report_csv_data = 'Fact Collection\n'
        get_report_csv_data += '1\n\n\n'
        get_report_csv_data += 'key\n'
        get_report_csv_data += 'value\n'

        get_report_csv_data = {'id': 1, 'report': [{'key': 'value'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       json=get_report_csv_data)
            nac = ReportSummaryCommand(SUBPARSER)
            args = Namespace(id='1', output_json=False, output_csv=True,
                             path=self.test_csv_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.FILE_SUCCESSFULLY_WRITTEN %
                                 self.test_csv_filename)
                with open(self.test_csv_filename, 'r') as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                    print(file_content_dict)
                self.assertDictEqual(get_report_csv_data, file_content_dict)

    def test_summary_report_output_directory(self):
        """Testing fail because output directory."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'summary',
                        '--json', '--output-file', '/']
            CLI().main()

    def test_summary_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'summary',
                        '--json', '--output-file', '/foo/bar/']
            CLI().main()

    def test_summary_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'summary',
                        '--json', '--output-file', '']
            CLI().main()
