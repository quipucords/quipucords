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
from api.models import Credential
import api.messages as messages


class CredentialTest(TestCase):
    """Tests against the Credential model and view set."""

    # pylint: disable= no-self-use,invalid-name
    def create_credential(self, name='test_cred',
                          username='testuser', password='testpass',
                          cred_type=Credential.NETWORK_CRED_TYPE):
        """Create a Credential model for use within test cases.

        :param name: name of the host credential
        :param username: the user used during the discovery and inspection
        :param password: the connection password
        :returns: A Credential model
        """
        return Credential.objects.create(name=name,
                                         cred_type=cred_type,
                                         username=username,
                                         password=password)

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('cred-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def test_hostcred_creation(self):
        """Tests the creation of a Credential model."""
        host_cred = self.create_credential()
        self.assertTrue(isinstance(host_cred, Credential))

    def test_hostcred_create(self):
        """Ensure we can create a new host credential object via API."""
        data = {'name': 'cred1',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

    def test_hostcred_create_double(self):
        """Create with duplicate name should fail."""
        data = {'name': 'cred1',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

        self.create_expect_400(data)

    def test_hc_create_err_name(self):
        """Test create without name.

        Ensure we cannot create a new host credential object without a name.
        """
        expected_error = {'name': ['This field is required.']}
        url = reverse('cred-list')
        data = {'username': 'user1',
                'password': 'pass1'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_username(self):
        """Test create without username.

        Ensure we cannot create a new host credential object without a
        username.
        """
        expected_error = {'username': ['This field is required.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'password': 'pass1'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_p_or_ssh(self):
        """Test API without password or keyfile.

        Ensure we cannot create a new host credential object without a password
        or an ssh_keyfile.
        """
        expected_error = {'non_field_errors': ['A host credential must have '
                                               'either a password or an '
                                               'ssh_keyfile.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'user1'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_err_ssh_bad(self):
        """Test API with bad sshkey.

        Ensure we cannot create a new host credential object an ssh_keyfile
        that cannot be found on the server.
        """
        expected_error = {'ssh_keyfile': ['ssh_keyfile, blah, is not a '
                                          'valid file on the system.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'user1',
                'ssh_keyfile': 'blah'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_long_name(self):
        """Test API with long name.

        Ensure we cannot create a new host credential object with a
        long name.
        """
        expected_error = {'name': ['Ensure this field has no more than '
                                   '64 characters.']}
        url = reverse('cred-list')
        data = {'name': 'A' * 100,
                'username': 'user1',
                'password': 'pass1'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_long_user(self):
        """Test API with long user.

        Ensure we cannot create a new host credential object with a
        long username.
        """
        expected_error = {'username': ['Ensure this field has no more than '
                                       '64 characters.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'A' * 100,
                'password': 'pass1'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_long_password(self):
        """Test api with long password.

        Ensure we cannot create a new host credential object with a
        long password.
        """
        expected_error = {'password': ['Ensure this field has no more than '
                                       '1024 characters.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'user1',
                'password': 'A' * 2000}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_long_sudo(self):
        """Test api with long sudo.

        Ensure we cannot create a new host credential object with a
        long sudo_password.
        """
        expected_error = {'sudo_password': ['Ensure this field has no more '
                                            'than 1024 characters.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'user1',
                'password': 'pass1',
                'sudo_password': 'A' * 2000}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hc_create_long_ssh(self):
        """Test api with long ssh.

        Ensure we cannot create a new host credential object with a
        long ssh_keyfile.
        """
        expected_error = {'ssh_keyfile': ['Ensure this field has no more than '
                                          '1024 characters.']}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'username': 'user1',
                'ssh_keyfile': 'A' * 2000}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_hostcred_list_view(self):
        """Tests the list view set of the Credential API."""
        url = reverse('cred-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hostcred_list_filter_view(self):
        """Tests the list view with filter set of the Credential API."""
        data = {'name': 'cred1',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)

        data = {'name': 'cred2',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user2',
                'password': 'pass2'}
        self.create_expect_201(data)

        url = reverse('cred-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_resp = resp.json()
        self.assertEqual(len(json_resp), 2)

        resp = self.client.get(
            url, {'cred_type': Credential.VCENTER_CRED_TYPE})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_resp = resp.json()
        self.assertEqual(len(json_resp), 1)

    def test_hostcred_update_view(self):
        """Tests the update view set of the Credential API."""
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)

        data = {'name': 'cred2',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user2',
                'password': 'pass2'}
        self.create_expect_201(data)

        data = {'name': 'cred2',
                'username': 'user23',
                'password': 'pass2'}
        url = reverse('cred-detail', args=(2,))
        resp = self.client.put(url, json.dumps(data),
                               content_type='application/json',
                               format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hostcred_update_double(self):
        """Update to new name that conflicts with other should fail."""
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)

        data = {'name': 'cred2',
                'cred_type': Credential.NETWORK_CRED_TYPE,
                'username': 'user2',
                'password': 'pass2'}
        self.create_expect_201(data)

        data = {'name': 'cred1',
                'username': 'user2',
                'password': 'pass2'}
        url = reverse('cred-detail', args=(2,))
        resp = self.client.put(url, json.dumps(data),
                               content_type='application/json',
                               format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hostcred_delete_view(self):
        """Tests the delete view set of the Credential API."""
        cred = Credential(name='cred2', username='user2',
                          password='pass2')
        cred.save()
        url = reverse('cred-detail', args=(cred.pk,))
        resp = self.client.delete(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_vcentercred_create(self):
        """Ensure we can create a new vcenter credential."""
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

    def test_vc_cred_create_double(self):
        """Vcenter cred with duplicate name should fail."""
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

        self.create_expect_400(data)

    def test_vc_create_missing_password(self):
        """Test VCenter without password."""
        expected_error = {'non_field_errors': [messages.VC_PWD_AND_USERNAME]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'ssh_keyfile': 'keyfile'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_vc_create_extra_keyfile(self):
        """Test VCenter without password."""
        expected_error = {'non_field_errors': [
            messages.VC_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'ssh_keyfile': 'keyfile'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_vc_create_extra_sudopass(self):
        """Test VCenter with extra sudo password."""
        expected_error = {'non_field_errors': [
            messages.VC_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'sudo_password': 'pass2'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_vc_create_extra_keyfile_pass(self):
        """Test VCenter with extra keyfile passphase."""
        expected_error = {'non_field_errors': [
            messages.VC_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.VCENTER_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'ssh_passphrase': 'pass2'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_sat_cred_create(self):
        """Ensure we can create a new satellite credential."""
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

    def test_sat_cred_create_double(self):
        """Satellite cred with duplicate name should fail."""
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1'}
        self.create_expect_201(data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().name, 'cred1')

        self.create_expect_400(data)

    def test_sat_create_missing_password(self):
        """Test Satellite without password."""
        expected_error = {'non_field_errors': [messages.SAT_PWD_AND_USERNAME]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'ssh_keyfile': 'keyfile'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_sat_create_extra_keyfile(self):
        """Test Satellite without password."""
        expected_error = {'non_field_errors': [
            messages.SAT_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'ssh_keyfile': 'keyfile'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_sat_create_extra_sudopass(self):
        """Test Satellite with extra sudo password."""
        expected_error = {'non_field_errors': [
            messages.SAT_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'sudo_password': 'pass2'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)

    def test_sat_create_extra_keyfile_pass(self):
        """Test Satellite with extra keyfile passphase."""
        expected_error = {'non_field_errors': [
            messages.SAT_KEY_FILE_NOT_ALLOWED]}
        url = reverse('cred-list')
        data = {'name': 'cred1',
                'cred_type': Credential.SATELLITE_CRED_TYPE,
                'username': 'user1',
                'password': 'pass1',
                'ssh_passphrase': 'pass2'}
        response = self.client.post(url, json.dumps(data),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_error)
