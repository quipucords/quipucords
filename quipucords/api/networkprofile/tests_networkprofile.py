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
"""Test the API application"""

import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from api.models import HostCredential


class NetworkProfileTest(TestCase):
    """Test the basic NetworkProfile infrastructure."""

    def setUp(self):
        self.cred = HostCredential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id
        self.cred_for_response = {'id': self.cred.id, 'name': self.cred.name}

    def create(self, data):
        """Utility function to call the create endpoint."""

        url = reverse('networkprofile-list')
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

        data = {'name': 'netprof1',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'credentials': [self.cred_for_upload]}
        response = self.create_expect_201(data)
        self.assertIn('id', response)

    def test_create_multiple_hosts(self):
        """A valid create request with two hosts."""

        data = {'name': 'netprof1',
                'hosts': ['1.2.3.4', '1.2.3.5'],
                'ssh_port': '22',
                'credentials': [self.cred_for_upload]}
        self.create_expect_201(data)

    def test_create_no_name(self):
        """A create request must have a name."""

        self.create_expect_400(
            {'hosts': '1.2.3.4',
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_unprintable_name(self):
        """The NetworkProfile name must be printable."""

        self.create_expect_400(
            {'name': '\r\n',
             'hosts': '1.2.3.4',
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_no_host(self):
        """A NetworkProfile needs a host."""

        self.create_expect_400(
            {'name': 'netprof1',
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_empty_host(self):
        """An empty string is not a host identifier."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': [],
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_long_name(self):
        """An long profile name."""

        self.create_expect_400(
            {'name': 'A' * 100,
             'hosts': ['1.2.3.4'],
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_negative_port(self):
        """An long profile name."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': ['1.2.3.4'],
             'ssh_port': -1,
             'credentials': [self.cred_for_upload]})

    def test_create_valid_hosts(self):
        """Test valid host patterns."""

        self.create_expect_201(
            {'name': 'netprof1',
             'hosts': ['10.10.181.9',
                       '10.10.181.9/16',
                       '10.10.128.[1:25]',
                       '10.10.[1:20].25',
                       '10.10.[1:20].[1:25]',
                       'localhost',
                       'mycentos.com',
                       'my-rhel[a:d].company.com',
                       'my-rhel[120:400].company.com'],
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})

    def test_create_invalid_hosts(self):
        """Test invalid host patterns."""

        hosts = ['192.1..2',
                 '192.01.5.10',
                 '192.1.5.1/',
                 '192.01.5.[1:10]/10',
                 '192.3.4.455',
                 '192.3.4.455/16',
                 '10.10.[181.9',
                 '10.10.128.[a:25]',
                 '10.10.[1-20].25',
                 '1.1.1.1/33',
                 'my_rhel[a:d].company.com',
                 'my-rhel[a:400].company.com']

        response = self.create(
            {'name': 'netprof1',
             'hosts': hosts,
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data['hosts']), len(hosts))

    def test_create_bad_host_pattern(self):
        """Test a invalid host pattern."""

        hosts = ['10.1.1.1-10.1.1.254']

        response = self.create(
            {'name': 'netprof1',
             'hosts': hosts,
             'ssh_port': '22',
             'credentials': [self.cred_for_upload]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data['hosts']), len(hosts))

    def test_create_no_ssh_port(self):
        """A NetworkProfile needs an ssh port."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': '1.2.3.4',
             'credentials': [self.cred_for_upload]})

    def test_create_bad_ssh_port(self):
        """-1 is not a valid ssh port."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': '1.2.3.4',
             'ssh_port': '-1',
             'credentials': [self.cred_for_upload]})

    def test_create_no_credentials(self):
        """A NetworkProfile needs credentials."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': '1.2.3.4',
             'ssh_port': '22'})

    def test_create_empty_credentials(self):
        """The empty string is not a valid credential list."""

        self.create_expect_400(
            {'name': 'netprof1',
             'hosts': '1.2.3.4',
             'ssh_port': '22',
             'credentials': []})

    def test_list(self):
        """List all NetworkProfile objects."""

        data = {'name': 'netprof',
                'ssh_port': '22',
                'hosts': ['1.2.3.4'],
                'credentials': [self.cred_for_upload]}
        for i in range(3):
            this_data = data.copy()
            this_data['name'] = 'netprof' + str(i)
            self.create_expect_201(this_data)

        url = reverse('networkprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = [{'id': 1, 'hosts': ['1.2.3.4'], 'credentials':
                     [{'id': 1, 'name': 'cred1'}], 'name': 'netprof0',
                     'ssh_port': 22},
                    {'id': 2, 'hosts': ['1.2.3.4'], 'credentials':
                     [{'id': 1, 'name': 'cred1'}], 'name': 'netprof1',
                     'ssh_port': 22},
                    {'id': 3, 'hosts': ['1.2.3.4'], 'credentials':
                     [{'id': 1, 'name': 'cred1'}], 'name': 'netprof2',
                     'ssh_port': 22}]
        self.assertEqual(content, expected)

    def test_retrieve(self):
        """Get details on a specific NetworkProfile by primary key."""

        initial = self.create_expect_201({
            'name': 'netprof1',
            'hosts': ['1.2.3.4'],
            'ssh_port': '22',
            'credentials': [self.cred_for_upload]})

        url = reverse('networkprofile-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('credentials', response.json())
        creds = response.json()['credentials']

        self.assertEqual(creds, [self.cred_for_response])

    # We don't have to test that update validates fields correctly
    # because the validation code is shared between create and update.
    def test_update(self):
        """Completely update a NetworkProfile."""

        initial = self.create_expect_201({
            'name': 'netprof2',
            'hosts': ['1.2.3.4'],
            'ssh_port': '22',
            'credentials': [self.cred_for_upload]})

        data = {'name': 'netprof2-new',
                'hosts': ['1.2.3.5'],
                'ssh_port': 22,
                'credentials': [self.cred.id]}
        url = reverse('networkprofile-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {'name': 'netprof2-new',
                    'hosts': ['1.2.3.5'],
                    'ssh_port': 22,
                    'credentials': [self.cred_for_response]}
        # data should be a strict subset of the response, because the
        # response adds an id field.
        for key, value in expected.items():  # pylint: disable=unused-variable
            self.assertEqual(expected[key], response.json()[key])

    def test_partial_update(self):
        """Partially update a NetworkProfile."""

        initial = self.create_expect_201({
            'name': 'netprof3',
            'hosts': ['1.2.3.4'],
            'ssh_port': '22',
            'credentials': [self.cred_for_upload]})

        data = {'name': 'netprof3-new',
                'hosts': ['1.2.3.5']}
        url = reverse('networkprofile-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], 'netprof3-new')
        self.assertEqual(response.json()['hosts'], ['1.2.3.5'])

    def test_delete(self):
        """Delete a NetworkProfile."""

        data = {'name': 'netprof3',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'credentials': [self.cred_for_upload]}
        response = self.create_expect_201(data)

        url = reverse('networkprofile-detail', args=(response['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
