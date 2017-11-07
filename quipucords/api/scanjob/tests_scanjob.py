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

import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from api.models import HostCredential, NetworkProfile


def dummy_start():
    """Create a dummy method for testing."""
    pass


class ScanJobTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = HostCredential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.network_profile = NetworkProfile(
            name='profile1',
            ssh_port=22)
        self.network_profile.save()
        self.network_profile.credentials.add(self.cred)

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('scanjob-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def create_expect_201(self, data):
        """Create a network profile, return the response as a dict."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def test_successful_create(self):
        """A valid create request should succeed."""
        data = {'profile': self.network_profile.id,
                'scan_type': 'discovery'}
        response = self.create_expect_201(data)
        self.assertIn('id', response)

    def test_create_no_profile(self):
        """A create request must have a profile."""
        self.create_expect_400(
            {})

    def test_create_invalid_scan_type(self):
        """A create request must have a valid scan_type."""
        data = {'profile': self.network_profile.id,
                'scan_type': 'foo'}
        self.create_expect_400(data)

    def test_create_default_host_type(self):
        """A valid create request should succeed with defaulted type."""
        data = {'profile': self.network_profile.id}
        response = self.create_expect_201(data)
        self.assertIn('id', response)
        self.assertIn('scan_type', response)
        self.assertEqual(response['scan_type'], 'host')

    def test_create_invalid_profile(self):
        """The NetworkProfile name must valid."""
        self.create_expect_400(
            {'profile': -1})

    def test_create_invalid_forks(self):
        """Test valid number of forks."""
        data = {'profile': self.network_profile.id,
                'max_concurrency': -5}
        self.create_expect_400(data)

    def test_list(self):
        """List all ScanJob objects."""
        data_default = {'profile': self.network_profile.id}
        data_discovery = {'profile': self.network_profile.id,
                          'scan_type': 'discovery'}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scanjob-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        print(content)
        expected = [{'id': 1,
                     'profile': {'id': 1, 'name': 'profile1'},
                     'scan_type': 'host',
                     'status': 'pending',
                     'max_concurrency': 50,
                     'systems_count': None,
                     'systems_scanned': None,
                     'fact_collection_id': None},
                    {'id': 2,
                     'profile': {'id': 1, 'name': 'profile1'},
                     'scan_type': 'discovery',
                     'status': 'pending',
                     'max_concurrency': 50,
                     'systems_count': None,
                     'systems_scanned': None,
                     'fact_collection_id': None}]
        self.assertEqual(content, expected)

    def test_retrieve(self):
        """Get details on a specific ScanJob by primary key."""
        data_discovery = {'profile': self.network_profile.id,
                          'scan_type': 'discovery'}
        initial = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile', response.json())
        profile = response.json()['profile']

        self.assertEqual(profile, {'id': 1, 'name': 'profile1'})

    def test_update_not_allowed(self):
        """Completely update a NetworkProfile."""
        data_discovery = {'profile': self.network_profile.id,
                          'scan_type': 'discovery'}
        initial = self.create_expect_201(data_discovery)

        data = {'profile': self.network_profile.id,
                'scan_type': 'host'}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update(self):
        """Partially update a ScanJob is not supported."""
        data_discovery = {'profile': self.network_profile.id,
                          'scan_type': 'discovery'}
        initial = self.create_expect_201(data_discovery)

        data = {'scan_type': 'host'}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete(self):
        """Delete a ScanJob is not supported."""
        data_discovery = {'profile': self.network_profile.id,
                          'scan_type': 'discovery'}
        response = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(response['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_pause_bad_state(self):
        """Pause a scanjob."""
        data_host = {'profile': self.network_profile.id, 'scan_type': 'host'}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}pause/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)
