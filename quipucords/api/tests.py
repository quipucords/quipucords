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
from . import models
from . import vault


class VaultTest(TestCase):
    """Tests against the vault class"""

    def test_encrypt_data_as_unicode(self):
        """Tests the encryption of sensitive data using SECRET_KEY"""
        value = vault.encrypt_data_as_unicode('encrypted data')
        self.assertTrue(isinstance(value, str))


class HostCredentialTest(TestCase):
    """ Tests against the HostCredential model and view set"""
    # pylint: disable= no-self-use
    def create_hostcredential(self, name="test_cred",
                              username="testuser", password="testpass"):
        """Creates a HostCredential model for use within test cases

        :param name: name of the host credential
        :param username: the user used during the discovery and inspection
        :param password: the connection password
        :returns: A HostCredential model
        """
        return models.HostCredential.objects.create(name=name,
                                                    username=username,
                                                    password=password)

    def test_hostcred_creation(self):
        """Tests the creation of a HostCredential model and asserts its type"""
        host_cred = self.create_hostcredential()
        self.assertTrue(isinstance(host_cred, models.HostCredential))

    def test_hostcred_create(self):
        """
        Ensure we can create a new host credential object via API.
        """
        url = reverse("hostcred-list")
        data = {'name': 'cred1',
                'username': 'user1',
                'password': 'pass1'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.HostCredential.objects.count(), 1)
        self.assertEqual(models.HostCredential.objects.get().name, 'cred1')

    def test_hc_create_err_name(self):
        """
        Ensure we cannot create a new host credential object without a name.
        """
        expected_error = {'name': ['This field is required.']}
        url = reverse("hostcred-list")
        data = {'username': 'user1',
                'password': 'pass1'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_username(self):
        """
        Ensure we cannot create a new host credential object without a
        username.
        """
        expected_error = {'username': ['This field is required.']}
        url = reverse("hostcred-list")
        data = {'name': 'cred1',
                'password': 'pass1'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_p_or_ssh(self):
        """
        Ensure we cannot create a new host credential object without a password
        or an ssh_keyfile.
        """
        expected_error = {'non_field_errors': ['A host credential must have '
                                               'either a password or an '
                                               'ssh_keyfile.']}
        url = reverse("hostcred-list")
        data = {'name': 'cred1',
                'username': 'user1'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_ssh_bad(self):
        """
        Ensure we cannot create a new host credential object an ssh_keyfile
        that cannot be found on the server.
        """
        expected_error = {'non_field_errors': ['ssh_keyfile, blah, is not a '
                                               'valid file on the system.']}
        url = reverse("hostcred-list")
        data = {'name': 'cred1',
                'username': 'user1',
                'ssh_keyfile': 'blah'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hostcred_list_view(self):
        """Tests the list view set of the HostCredential API"""
        url = reverse("hostcred-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hostcred_update_view(self):
        """Tests the update view set of the HostCredential API"""
        cred = models.HostCredential(name='cred2', username='user2',
                                     password='pass2')
        cred.save()
        data = {'name': 'cred2',
                'username': 'user2',
                'password': 'pass3'}
        url = reverse("hostcred-detail", args=(cred.pk,))
        resp = self.client.put(url, json.dumps(data),
                               content_type='application/json',
                               format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hostcred_delete_view(self):
        """Tests the delete view set of the HostCredential API"""
        cred = models.HostCredential(name='cred2', username='user2',
                                     password='pass2')
        cred.save()
        url = reverse("hostcred-detail", args=(cred.pk,))
        resp = self.client.delete(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class NetworkProfileTest(TestCase):
    """Test the basic NetworkProfile infrastructure."""

    def setUp(self):
        self.cred = models.HostCredential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = {
            'id': self.cred.id
        }

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

        content = json.loads(response.content)
        self.assertGreaterEqual(len(content), 3)

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

        self.assertEqual(creds,
                         [{'id': self.cred.id,
                           'name': self.cred.name}])

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
                'credentials': [{
                    'id': self.cred.id,
                    'name': self.cred.name}]}
        url = reverse('networkprofile-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # data should be a strict subset of the response, because the
        # response adds an id field.
        for key, value in data.items():
            self.assertEqual(data[key], response.json()[key])

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
