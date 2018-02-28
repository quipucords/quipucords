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
"""Test the API application."""

import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from api.models import (Credential,
                        Source,
                        ScanTask,
                        ScanOptions)
from api.scan.view import (expand_scan)
from api.scan.serializer import ScanSerializer
from scanner.test_util import create_scan_job

# pylint: disable=unused-argument,invalid-name


class ScanTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = Credential.objects.create(
            name='cred1',
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.source = Source(
            name='source1',
            source_type='network',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('scan-list')
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
        """Create a scan, return the response as a dict."""
        response = self.create(data)
        response_json = response.json()
        if response.status_code != status.HTTP_201_CREATED:
            print('Cause of failure: ')
            print(response_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response_json

    def test_successful_create(self):
        """A valid create request should succeed."""
        data = {'name': 'test', 'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        response = self.create_expect_201(data)
        self.assertIn('id', response)

    def test_create_no_name(self):
        """A create request must have a name."""
        self.create_expect_400(
            {'sources': [self.source.id]},
            {'name': ['This field is required.']})

    def test_create_no_source(self):
        """A create request must have a source."""
        self.create_expect_400(
            {'name': 'test'}, {'sources': ['This field is required.']})

    def test_create_invalid_scan_type(self):
        """A create request must have a valid scan_type."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'scan_type': 'foo',
                'options': {'disable_optional_products': {'jboss_eap': True,
                                                          'jboss_fuse': True,
                                                          'jboss_brms': True}}}
        self.create_expect_400(
            data, {'scan_type': ['foo, is an invalid choice. '
                                 'Valid values are connect,inspect.']})

    def test_create_blank_scan_type(self):
        """A create request must not have a blank scan_type."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'scan_type': ''}
        self.create_expect_400(
            data, {'scan_type': ['This field may not be blank. '
                                 'Valid values are connect,inspect.']})

    def test_create_invalid_srcs_type(self):
        """A create request must have integer ids."""
        data = {'name': 'test',
                'sources': ['foo'],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_400(
            data, {'sources': ['Source identifiers must be integer values.']})

    def test_create_invalid_srcs_id(self):
        """A create request must have vaild ids."""
        data = {'name': 'test',
                'sources': [100000],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_400(
            data, {'sources': ['Source with id=100000 could '
                               'not be found in database.']})

    def test_create_default_host_type(self):
        """A valid create request should succeed with defaulted type."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'options': {'disable_optional_products': {'jboss_eap': True,
                                                          'jboss_fuse': True,
                                                          'jboss_brms': True}}}
        response = self.create_expect_201(data)
        self.assertIn('id', response)
        self.assertIn('scan_type', response)
        self.assertEqual(response['scan_type'], ScanTask.SCAN_TYPE_INSPECT)

    def test_create_invalid_source(self):
        """The Source name must valid."""
        self.create_expect_400(
            {'name': 'test',
             'sources': -1},
            {'sources':
             ['Expected a list of items but got type "int".']})

    def test_create_invalid_forks(self):
        """Test valid number of forks."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'options': {'max_concurrency': -5,
                            'disable_optional_products': {'jboss_eap': True}}}
        self.create_expect_400(data, {
            'options': {'max_concurrency':
                        ['Ensure this value is greater than or equal '
                         'to 1.']}})

    def test_create_invalid_disable_optional_products_type(self):
        """Test invalid type for disable_optional_products type."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'options': {'disable_optional_products': 'foo'}}
        self.create_expect_400(data, {
            'options': {'disable_optional_products':
                        ['Extra vars must be a dictionary.']}})

    def test_create_invalid_disable_optional_products_key(self):
        """Test invalid type for disable_optional_products key."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'options': {'disable_optional_products': {'foo': True}}}
        self.create_expect_400(data, {
            'options': {'disable_optional_products':
                        ['Extra vars keys must be jboss_eap,'
                         ' jboss_fuse, or jboss_brms.']}})

    def test_create_invalid_disable_optional_products_val(self):
        """Test invalid type for disable_optional_products value."""
        data = {'name': 'test',
                'sources': [self.source.id],
                'options': {'disable_optional_products':
                            {'jboss_eap': 'True'}}}
        self.create_expect_400(data, {
            'options': {'disable_optional_products':
                        ['Extra vars values must be type boolean.']}})

    def test_get_optional_products(self):
        """Test the get_optional_products method when arg is None."""
        disable_optional_products = None
        expected = {}
        content = ScanOptions.get_optional_products(disable_optional_products)
        self.assertEqual(content, expected)

    def test_list(self):
        """List all scan objects."""
        data_default = {'name': 'test1',
                        'sources': [self.source.id]}
        data_discovery = {'name': 'test2',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [{'id': 1, 'name':
                     'test1',
                     'sources': [{'id': 1,
                                  'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': 'inspect',
                     'options': {'max_concurrency': 50,
                                 'enable_extended_product_search':
                                 {'jboss_eap': False,
                                  'jboss_fuse': False,
                                  'jboss_brms': False}}},
                    {'id': 2, 'name':
                     'test2',
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': 'connect',
                     'options': {'max_concurrency': 50,
                                 'enable_extended_product_search':
                                 {'jboss_eap': False,
                                  'jboss_fuse': False,
                                  'jboss_brms': False}}}]
        expected = {'count': 2,
                    'next': None,
                    'previous': None,
                    'results': results1}
        self.assertEqual(content, expected)

    def test_filtered_list(self):
        """List filtered Scan objects."""
        data_default = {'name': 'test1',
                        'sources': [self.source.id]}
        data_discovery = {'name': 'test2',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scan-list')
        response = self.client.get(
            url, {'scan_type': ScanTask.SCAN_TYPE_CONNECT})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [{'id': 2,
                     'name': 'test2',
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': 'connect',
                     'options': {
                         'max_concurrency': 50,
                         'enable_extended_product_search':
                         {'jboss_eap': False,
                          'jboss_fuse': False,
                          'jboss_brms': False}}}]
        expected = {'count': 1,
                    'next': None,
                    'previous': None,
                    'results': results1}
        self.assertEqual(content, expected)

    def test_retrieve(self):
        """Get Scan details by primary key."""
        data_discovery = {'name': 'test',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        initial = self.create_expect_201(data_discovery)

        url = reverse('scan-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sources', response.json())
        sources = response.json()['sources']

        self.assertEqual(
            sources, [{'id': 1, 'name': 'source1', 'source_type': 'network'}])

    def test_retrieve_bad_id(self):
        """Get Scan details by bad primary key."""
        url = reverse('scan-detail', args=('string',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update(self):
        """Completely update a scan."""
        data_discovery = {'name': 'test',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        initial = self.create_expect_201(data_discovery)

        data = {'name': 'test2',
                'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                'options': {'disable_optional_products':
                            {'jboss_eap': False,
                             'jboss_fuse': True,
                             'jboss_brms': True}}}
        url = reverse('scan-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        response_json = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)
        self.assertEqual(response_json.get('scan_type'),
                         ScanTask.SCAN_TYPE_INSPECT)
        self.assertEqual(response_json.get('name'), 'test2')
        self.assertFalse(response_json.get('options').get('jboss_eap'))

    def test_partial_update(self):
        """Test partial update a scan."""
        data_discovery = {'name': 'test',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        initial = self.create_expect_201(data_discovery)

        data = {'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        url = reverse('scan-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json.get('scan_type'),
                         ScanTask.SCAN_TYPE_INSPECT)
        data = {'name': 'test2',
                'options': {'disable_optional_products':
                            {'jboss_eap': False,
                             'jboss_fuse': True,
                             'jboss_brms': True}}}
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        response_json = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)
        self.assertEqual(response_json.get('name'), 'test2')
        self.assertFalse(response_json.get('options').get('jboss_eap'))

    def test_expand_scan(self):
        """Test view expand_scan."""
        scan_job, scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT)

        scan_task.update_stats('TEST_VC.', sys_count=2, sys_failed=1,
                               sys_scanned=1)

        serializer = ScanSerializer(scan_job.scan)
        json_scan = serializer.data
        json_scan = expand_scan(json_scan)

        self.assertEqual(json_scan.get(
            'sources').first().get('name'), 'source1')
        self.assertEqual(
            json_scan.get('most_recent'),
            {'id': 1,
             'systems_count': 2,
             'systems_scanned': 1,
             'systems_failed': 1,
             'status': 'pending'})

    def test_delete(self):
        """Delete a scan."""
        data_discovery = {'name': 'test',
                          'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        response = self.create_expect_201(data_discovery)

        url = reverse('scan-detail', args=(response['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT)
