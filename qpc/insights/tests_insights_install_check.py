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

import unittest

from qpc.insights.utils import check_insights_install


class InsightsUploadCliTests(unittest.TestCase):
    """Class for testing the validation for install of insights-client."""

    def setUp(self):
        """Create test setup."""
        pass

    def tearDown(self):
        """Remove test setup."""
        pass

    def test_check_insights_install(self):
        """Testing if insights is installed correctly."""
        # pylint:disable=line-too-long
        successful_install = 'Could not reach the Insights service to register.\nRunning connection test...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'  # noqa: E501
        test = check_insights_install(successful_install)
        self.assertEqual(test, True)

    def test_check_insights_install_error_no_command(self):
        """Testing error response no command found."""
        no_command_return = 'insights-client: command not found'
        test = check_insights_install(no_command_return)
        self.assertEqual(test, False)

    def test_check_insights_install_no_module(self):
        """Testing error response no modules found."""
        no_module_return = 'ModuleNotFoundError: No module named \'insights\''
        test = check_insights_install(no_module_return)
        self.assertEqual(test, False)

    def test_check_insights_install_failed_connection(self):
        """Testing error response if bad connection."""
        # pylint:disable=line-too-long
        bad_connection_return = 'Running connection test...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 401\nHTTP Status Text: Unauthorized\nHTTP Response Text: \nConnection failed\n=== End Upload URL Connection Test: FAILURE ===\n\n=== Begin API URL Connection Test ===\nHTTP  Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed with some errors\nSee /var/log/insights-client/insights-client.log for more details.\n'  # noqa: E501
        test = check_insights_install(bad_connection_return)
        self.assertEqual(test, False)
