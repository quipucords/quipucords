import json
from datetime import datetime
from unittest.mock import patch

import api.messages as messages
from api.models import (Credential,
                        Scan,
                        ScanTask,
                        Source)
from api.serializers import SourceSerializer
from api.source.view import format_source

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status


from scanner.test_util import create_scan_job

def dummy_start():
    """Create a dummy method for testing."""
    pass

class SourceTest(TestCase):

    def setUp(self):
        """Create test case setup."""
        self.net_cred = Credential.objects.create(
            name='net_cred1',
            cred_type=Credential.NETWORK_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.net_cred_for_upload = self.net_cred.id
        self.net_cred_for_response = {'id': self.net_cred.id,
                                      'name': self.net_cred.name}

        self.vc_cred = Credential.objects.create(
            name='vc_cred1',
            cred_type=Credential.VCENTER_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.vc_cred_for_upload = self.vc_cred.id
        self.vc_cred_for_response = {'id': self.vc_cred.id,
                                     'name': self.vc_cred.name}

        self.sat_cred = Credential.objects.create(
            name='sat_cred1',
            cred_type=Credential.SATELLITE_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.sat_cred_for_upload = self.sat_cred.id
        self.sat_cred_for_response = {'id': self.sat_cred.id,
                                      'name': self.sat_cred.name}

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('source-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data, expected_response=None):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if response.status_code != 400:
            print(response.json())
        if expected_response:
            response_json = response.json()
            self.assertEqual(response_json, expected_response)

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != 201:
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    # pylint: disable=unused-argument
    @patch('api.source.view.start_scan', side_effect=dummy_start)
    def create_with_query(self, query, data, start_scan):
        """Create a source with query param.

        :param query: The value of scan
        :param data: The payload of the source
        :return a dict containing the response
        """
        url = reverse('source-list')
        url += query
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    # pylint: disable=no-value-for-parameter
    def create_expect_201_with_query(self, query, data):
        """Create a valid source with a scan parameter."""
        response = self.create_with_query(query, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    # pylint: disable=no-value-for-parameter
    def create_expect_400_with_query(self,
                                     query,
                                     data,
                                     expected_response=None):
        """Create an expect HTTP 400."""
        response = self.create_with_query(query, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if expected_response:
            response_json = response.json()
            self.assertEqual(response_json, expected_response)


    def test_create_valid_hosts(self):
        """Test valid host patterns."""
        self.create_expect_201(
            {'name': 'source1',
             'source_type': Source.NETWORK_SOURCE_TYPE,
             'hosts': ['10.10.181.9',
                       '10.10.181.9/16',
                       '10.10.128.[1:25]',
                       '10.10.[1:20].25',
                       '10.10.[1:20].[1:25]',
                       'localhost',
                       'mycentos.com',
                       'my-rhel[a:d].company.com',
                       'my-rhel[120:400].company.com'],
             'exclude_hosts': ['10.10.191.9'],
             'port': '22',
             'credentials': [self.net_cred_for_upload]})
