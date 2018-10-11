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
"""Test the report API."""

import json
from unittest.mock import patch

from api import messages
from api.models import (Credential,
                        ScanTask,
                        ServerInformation,
                        Source)

from django.core import management
from django.test import TestCase

from rest_framework import status

from scanner.test_util import create_scan_job


def dummy_start():
    """Create a dummy method for testing."""
    pass


class AsyncMergeReports(TestCase):
    """Tests against the Deployment reports function."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
        self.net_source = Source.objects.create(
            name='test_source', source_type=Source.NETWORK_SOURCE_TYPE)

        self.net_cred = Credential.objects.create(
            name='net_cred1',
            cred_type=Credential.NETWORK_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.net_source.credentials.add(self.net_cred)

        self.net_source.hosts = '["1.2.3.4"]'
        self.net_source.save()
        self.server_id = ServerInformation.create_or_retreive_server_id()

    def create_report_merge_job(self, data):
        """Call the create endpoint."""
        url = '/api/v1/reports/merge/jobs/'
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_report_merge_job_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_report_merge_job(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def create_report_merge_job_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_report_merge_job(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    ##############################################################
    # Test Async Report Merge
    ##############################################################

    @patch('api.report.view.start_scan', side_effect=dummy_start)
    def test_greenpath_create(self, start_scan):
        """Create report merge job object via API."""
        # pylint: disable=unused-argument
        request_json = {'sources':
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_report_merge_job_expect_201(
            request_json)

        expected = {
            'scan_type': 'fingerprint',
            'status': 'created',
            'status_message': 'Job is created.'
        }
        self.assertIn('id', response_json)
        job_id = response_json.pop('id')
        self.assertEqual(response_json, expected)

        url = '/api/v1/reports/merge/jobs/{}/'.format(job_id)
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_200_OK)

    def test_404_if_not_fingerprint_job(self):
        """Test report job status only returns merge jobs."""
        source = Source(
            name='source1',
            hosts=json.dumps(['1.2.3.4']),
            source_type='network',
            port=22)
        source.save()
        scan_job, _ = create_scan_job(
            source, scan_type=ScanTask.SCAN_TYPE_INSPECT)

        url = '/api/v1/reports/merge/jobs/{}/'.format(scan_job.id)
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_404_NOT_FOUND)

        scan_job.scan_type = ScanTask.SCAN_TYPE_FINGERPRINT
        scan_job.save()
        url = '/api/v1/reports/merge/jobs/{}/'.format(scan_job.id)
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_200_OK)

    def test_create_report_merge_bad_url(self):
        """Create merge report job bad url."""
        url = '/api/v1/reports/merge/jobs/1/'
        get_response = self.client.post(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_missing_sources(self):
        """Test missing sources attribute."""
        request_json = {}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_sources(self):
        """Test empty sources attribute."""
        request_json = {'sources': []}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_missing_name(self):
        """Test source is missing source_name."""
        request_json = {'sources': [{'foo': 'abc'}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_name(self):
        """Test source has empty source_name."""
        request_json = {'sources': [{'source_name': ''}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_name_not_string(self):
        """Test source has source_name that is not a string."""
        request_json = {'sources': [{'server_id': self.server_id,
                                     'source_name': 100,
                                     'source_type':
                                     self.net_source.source_type}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_SOURCE_NAME_NOT_STR)

    def test_missing_source_type(self):
        """Test source_type is missing."""
        request_json = {'sources': [
            {'source_name': self.net_source.name}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_source_type(self):
        """Test source_type is empty."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': ''}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_invalid_source_type(self):
        """Test source_type has invalid_value."""
        request_json = {'sources':
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
                          'source_type': 'abc'}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)

        valid_choices = ', '.join(
            [valid_type[0] for valid_type in Source.SOURCE_TYPE_CHOICES])

        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_MUST_BE_ONE_OF % valid_choices)

    def test_source_missing_facts(self):
        """Test source missing facts attr."""
        request_json = {'sources':
                        [{'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_facts(self):
        """Test source has empty facts list."""
        request_json = {'sources':
                        [{'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type,
                          'facts': []}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)
