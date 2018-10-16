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
from unittest.mock import patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100

from qpc import messages
from qpc.insights import REPORT_URI
from qpc.insights.upload import InsightsUploadCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class InsightsUploadCliTests(unittest.TestCase):
    """Class for testing the scan job commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_report(self, subprocess):
        """Testing response with a vaild report id."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       json=get_report_json_data)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             test=True)
            # pylint:disable=line-too-long
            subprocess.return_value.communicate.return_value = (None, b'Could not reach the Insights service to register.\nRunning connection test...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n')  # noqa E501
            subprocess.return_value.returncode = 0
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.GOOD_INSIGHTS_CHECK.replace('%s', ''),
                              report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_invalid_report(self, subprocess):
        """Testing error response with an invalid report id."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=404, json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             test=True)
            # pylint:disable=line-too-long
            subprocess.return_value.communicate.return_value = (None, b'Could not reach the Insights service to register.\nRunning connection test...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n')  # noqa E501
            subprocess.return_value.returncode = 0
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.INSIGHTS_REPORT_NOT_FOUND %
                          ('1'), report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unknown_error(self, subprocess):
        """Testing error response with an invalid report id."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400, json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             test=True)
            subprocess.return_value.communicate.return_value = \
                (None, b'Unknown Error')
            subprocess.return_value.returncode = 1
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.BAD_INSIGHTS_CHECK %
                          ('Unknown Error'), report_out.getvalue())
