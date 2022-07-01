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

from api import messages
from api.common.common_report import create_report_version
from api.models import (Credential,
                        ServerInformation,
                        Source)

from django.core import management
from django.test import TestCase
from django.urls import reverse

from rest_framework import status


class SyncMergeReports(TestCase):
    """Tests merging reports synchronously."""

    # pylint: disable=invalid-name
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

    def create_details_report(self, data):
        """Call the create endpoint."""
        url = reverse('reports-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_details_report_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_details_report(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    ##############################################################
    # Test Report Merge
    ##############################################################
    def test_sync_merge_empty_body(self):
        """Test sync merge with empty body."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_REQUIRED]})

    def test_sync_merge_empty_dict(self):
        """Test sync merge with empty dict."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_REQUIRED]})

    def test_sync_merge_jobs_not_list(self):
        """Test sync merge with not list."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': 5}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_LIST]})

    def test_sync_merge_jobs_list_too_short(self):
        """Test sync merge with list too short."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_TOO_SHORT]})

    def test_sync_merge_jobs_list_contains_string(self):
        """Test sync merge with containing str."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 'hello']}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_INT]})

    def test_sync_merge_jobs_list_contains_duplicates(self):
        """Test sync merge with containing duplicates."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 5]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_UNIQUE]})

    def test_sync_merge_jobs_list_contains_invalid_job_ids(self):
        """Test sync merge with containing duplicates."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 6]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports':
                            [messages.REPORT_MERGE_NOT_FOUND % '5, 6']})

    def test_sync_merge_jobs_success(self):
        """Test sync merge jobs success."""
        url = reverse('reports-list')
        sources1 = [{'server_id': self.server_id,
                     'report_version': create_report_version(),
                     'source_name': self.net_source.name,
                     'source_type': self.net_source.source_type,
                     'facts': [{'key1': 'value1'}]}]
        sources2 = [{'server_id': 'abc',
                     'report_version': create_report_version(),
                     'source_name': 'another_name',
                     'source_type': 'network',
                     'facts': [{'key2': 'value2'}]}]
        request_json = {'report_type': 'details',
                        'sources': sources1}
        response = self.client.post(url,
                                    json.dumps(request_json),
                                    'application/json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(
            response_json['sources'],
            sources1)
        report1_id = response_json['report_id']

        request_json = {'report_type': 'details',
                        'sources': sources2}
        response = self.client.post(url,
                                    json.dumps(request_json),
                                    'application/json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(
            response_json['sources'],
            sources2)
        report2_id = response_json['report_id']

        url = '/api/v1/reports/merge/'
        data = {'reports': [report1_id, report2_id]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        json_response = response.json()
        expected = {'report_id': 3,
                    'report_platform_id': json_response.get(
                        'report_platform_id'),
                    'report_type': 'details',
                    'report_version': create_report_version(),
                    'sources': [
                        {'server_id': 'abc',
                         'report_version': create_report_version(),
                         'source_name': 'another_name',
                         'source_type': 'network',
                         'facts': [{'key2': 'value2'}]},
                        {'server_id': self.server_id,
                         'report_version': create_report_version(),
                         'source_name': 'test_source',
                         'source_type': 'network',
                         'facts': [{'key1': 'value1'}]}]}

        self.assertEqual(
            json_response, expected)
