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
"""Test the fact API."""

import json

import api.messages as messages
from api.models import (Credential,
                        FactCollection,
                        Source)

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status


class FactCollectionTest(TestCase):
    """Tests against the FactCollection model and view set."""

    # pylint: disable=no-self-use,too-many-arguments,invalid-name
    # pylint: disable=too-many-locals,too-many-branches

    def setUp(self):
        """Create test case setup."""
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

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('facts-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_json = response.json()
        if expected_response:
            self.assertEqual(response_json, expected_response)
        return response_json

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def retrieve_expect_200(self, identifier):
        """Create a source, return the response as a dict."""
        url = reverse('facts-detail', args=(identifier,))
        response = self.client.get(url)

        if response.status_code != status.HTTP_200_OK:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    ################################################################
    # Test Model Create
    ################################################################
    def test_greenpath_create(self):
        """Create fact collection object via API."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_expect_201(
            request_json)
        self.assertEqual(
            response_json['sources'],
            request_json['sources'])
        self.assertEqual(FactCollection.objects.count(), 1)

    def test_missing_sources(self):
        """Test missing sources attribute."""
        request_json = {}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_sources(self):
        """Test empty sources attribute."""
        request_json = {'sources': []}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_missing_id(self):
        """Test source is missing source_id."""
        request_json = {'sources': [{'foo': 'abc'}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_id'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_id(self):
        """Test source has empty source_id."""
        request_json = {'sources': [{'source_id': ''}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_id'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_id_not_int(self):
        """Test source has source_id not int."""
        request_json = {'sources': [{'source_id': 'abc'}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_id'],
            messages.FC_SOURCE_ID_NOT_INT)

    def test_source_id_not_exist(self):
        """Test source_id is not back by model object."""
        request_json = {'sources': [{'source_id': 42}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_id'],
            messages.FC_SOURCE_NOT_FOUND % 42)

    def test_missing_source_type(self):
        """Test source_type is missing."""
        request_json = {'sources': [
            {'source_id': self.net_source.id}]}
        response_json = self.create_expect_400(
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
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_invalid_source_type(self):
        """Test source_type has invalid_value."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': 'abc'}]}
        response_json = self.create_expect_400(
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
                        [{'source_id': self.net_source.id,
                          'source_type': self.net_source.source_type}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_facts(self):
        """Test source has empty facts list."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': self.net_source.source_type,
                          'facts': []}]}
        response_json = self.create_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)
