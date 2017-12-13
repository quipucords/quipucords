#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the API application."""

from unittest.mock import patch
import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from api.models import Credential, Source, ScanTask


def dummy_start():
    """Create a dummy method for testing."""
    pass


# pylint: disable=unused-argument
class ScanJobTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = Credential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.source = Source(
            name='source1',
            source_type='network',
            ssh_port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('scanjob-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data, expected_response):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_json = response.json()
        self.assertEqual(response_json, expected_response)

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        response_json = response.json()
        if response.status_code != status.HTTP_201_CREATED:
            print('Cause of failure: ')
            print(response_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response_json

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_successful_create(self, start_scan):
        """A valid create request should succeed."""
        data = {'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        response = self.create_expect_201(data)
        self.assertIn('id', response)

    def test_create_no_source(self):
        """A create request must have a source."""
        self.create_expect_400(
            {}, {'sources': ['This field is required.']})

    def test_create_invalid_scan_type(self):
        """A create request must have a valid scan_type."""
        data = {'sources': [self.source.id],
                'scan_type': 'foo'}
        self.create_expect_400(
            data, {'scan_type': ['"foo" is not a valid choice.']})

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_create_default_host_type(self, start_scan):
        """A valid create request should succeed with defaulted type."""
        data = {'sources': [self.source.id]}
        response = self.create_expect_201(data)
        self.assertIn('id', response)
        self.assertIn('scan_type', response)
        self.assertEqual(response['scan_type'], ScanTask.SCAN_TYPE_INSPECT)

    def test_create_invalid_source(self):
        """The Source name must valid."""
        self.create_expect_400(
            {'sources': -1},
            {'sources':
             ['Expected a list of items but got type "int".']})

    def test_create_invalid_forks(self):
        """Test valid number of forks."""
        data = {'sources': [self.source.id],
                'options': {'max_concurrency': -5}}
        self.create_expect_400(data, {
            'options': {'max_concurrency':
                        ['Ensure this value is greater than or equal '
                         'to 1.']}})

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_list(self, start_scan):
        """List all ScanJob objects."""
        data_default = {'sources': [self.source.id]}
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scanjob-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        print(content)
        expected = [{'id': 1,
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'status': 'created'},
                    {'id': 2,
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                     'status': 'created'}]
        self.assertEqual(content, expected)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_retrieve(self, start_scan):
        """Get details on a specific ScanJob by primary key."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        initial = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sources', response.json())
        sources = response.json()['sources']

        self.assertEqual(
            sources, [{'id': 1, 'name': 'source1', 'source_type': 'network'}])

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_update_not_allowed(self, start_scan):
        """Completely update a Source."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        initial = self.create_expect_201(data_discovery)

        data = {'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_partial_update(self, start_scan):
        """Partially update a ScanJob is not supported."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        initial = self.create_expect_201(data_discovery)

        data = {'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_delete(self, start_scan):
        """Delete a ScanJob is not supported."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        response = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(response['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_pause_bad_state(self, start_scan):
        """Pause a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}pause/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_cancel(self, start_scan):
        """Cancel a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}cancel/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_restart_bad_state(self, start_scan):
        """Restart a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}restart/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)
