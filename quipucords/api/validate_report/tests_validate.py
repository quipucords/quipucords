#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the the validate reports API."""

import json

from django.core import management
from django.test import TestCase

from rest_framework import status


class ValidateReportsTest(TestCase):
    """Tests against validating a report."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')

    def tearDown(self):
        """Create test case tearDown."""
        pass

    def test_validate_report_mismatch(self):
        """Test the validate endpoint mismatch report and hash."""
        url = '/api/v1/reports/validate/'
        data = {'report': 'foo',
                'hash': 'bar'}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertEqual(
            json_response['detail'], False)

    def test_validate_report_match(self):
        """Test the validate endpoint correct report and hash."""
        url = '/api/v1/reports/validate/'
        data = {
            'report': 'fake report contents',
            'hash':
            '47e852b4bfb727713c496456010997cbe42fc585ff6471fff5f496314cc54a9f'}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertEqual(
            json_response['detail'], True)

    def test_validate_report_none(self):
        """Test the validate endpoint missing hash."""
        url = '/api/v1/reports/validate/'
        data = {'report': 'fake report contents'}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_424_FAILED_DEPENDENCY)
        json_response = response.json()
        self.assertEqual(
            json_response['detail'],
            'A report and hash must be provided to validate.')
