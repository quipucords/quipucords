"""Test the API application."""

import random
from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status

from api import messages
from api.models import Credential, Source
from api.vault import decrypt_data_as_unicode
from constants import ENCRYPTED_DATA_MASK, DataSources
from tests.factories import CredentialFactory, SourceFactory

ACCEPT_JSON_HEADER = {"Accept": "application/json"}


def alt_cred_type(cred_type):
    """Given a credential type, return an alternate random one."""
    cred_types = DataSources.values.copy()
    cred_types.remove(cred_type)
    return random.choice(cred_types)


def generate_openssh_pkey(faker):
    """Generate a random OpenSSH private key."""
    pkey = "-----BEGIN OPENSSH EXAMPLE KEY-----\n"
    for _ in range(5):
        pkey += f"{faker.lexify('?' * 70)}\n"
    pkey += "-----END OPENSSH EXAMPLE KEY-----"
    return pkey


@pytest.mark.django_db
class TestCredential:
    """Tests against the Credential model and view set."""

    def create_credential(
        self,
        name="test_cred",
        username="testuser",
        password="testpass",
        cred_type=DataSources.NETWORK,
    ):
        """Create a Credential model for use within test cases.

        :param name: name of the host credential
        :param username: the user used during the discovery and inspection
        :param password: the connection password
        :returns: A Credential model
        """
        return Credential.objects.create(
            name=name, cred_type=cred_type, username=username, password=password
        )

    def update_credential(self, name=None, username=None, password=None):
        """Update a Credential object.

        :param name: name of the host credential
        :param username: the user used during the discovery and inspection
        :param password: the connection password
        :returns: A Credential model
        """
        return Credential.objects.update(
            name=name, username=username, password=password
        )

    def create(self, data, django_client):
        """Call the create endpoint."""
        url = reverse("cred-list")
        return django_client.post(url, json=data)

    def create_expect_400(self, data, django_client):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data, django_client)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def create_expect_201(self, data, django_client):
        """Create a source, return the response as a dict."""
        response = self.create(data, django_client)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def test_hostcred_creation(self):
        """Tests the creation of a Credential model."""
        host_cred = self.create_credential()
        assert isinstance(host_cred, Credential)

    def test_hostcred_create(self, django_client):
        """Ensure we can create a new host credential object via API."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

    @pytest.fixture
    def openssh_key(self, faker):
        """Return an openssh_key random OpenSSH private key."""
        return generate_openssh_pkey(faker)

    @pytest.fixture
    def updated_openssh_key(self, faker):
        """Return an openssh_key random OpenSSH private key."""
        return generate_openssh_pkey(faker)

    def test_hostcred_create_with_ssh_keyvalue(self, django_client, openssh_key):
        """Ensure we can create a new host credential object with an ssh_keyvalue."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "ssh_keyvalue": openssh_key,
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1

        cred = Credential.objects.get()
        assert cred.name == "cred1"
        assert decrypt_data_as_unicode(cred.ssh_keyvalue) == openssh_key

    def test_hostcred_create_with_ssh_keyvalue_and_passphrase(
        self, django_client, faker, openssh_key
    ):
        """Ensure we create a new credential with an ssh_keyvalue with a passphrase."""
        ssh_passphrase = faker.password(length=32)
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "ssh_keyvalue": openssh_key,
            "ssh_passphrase": ssh_passphrase,
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1

        cred = Credential.objects.get()
        assert cred.name == "cred1"
        assert decrypt_data_as_unicode(cred.ssh_keyvalue) == openssh_key
        assert decrypt_data_as_unicode(cred.ssh_passphrase) == ssh_passphrase

    def test_hostcred_create_double(self, django_client):
        """Create with duplicate name should fail."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

        self.create_expect_400(data, django_client)

    def test_hc_create_err_name(self, django_client):
        """Test create without name.

        Ensure we cannot create a new host credential object without a name.
        """
        expected_error = {"name": ["This field is required."]}
        url = reverse("cred-list")
        data = {
            "username": "user1",
            "password": "pass1",
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_err_username(self, django_client):
        """Test create without username.

        Ensure we cannot create a new host credential object without a
        username.
        """
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "password": "pass1",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["username"]

    def test_hc_create_err_p_or_ssh(self, django_client):
        """Test API without password, ssh_keyfile or ssh_keyvalue.

        Ensure we cannot create a new host credential object without a password,
        an ssh_keyfile, or an ssh_keyvalue.
        """
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        assert response.json()["non_field_errors"] == [
            messages.HC_PWD_OR_KEYFILE_OR_KEYVALUE
        ]

    def test_hc_create_err_ssh_bad(self, django_client):
        """Test API with bad sshkey.

        Ensure we cannot create a new host credential object an ssh_keyfile
        that cannot be found on the server.
        """
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
            "ssh_keyfile": "blah",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_keyfile"]

    def test_hc_create_err_ssh_keyfile_and_keyvalue(
        self, tmp_path, django_client, faker, openssh_key
    ):
        """Test API with both ssh_keyfile and ssh_keyvalue.

        Ensure we cannot create a new host credential object with both
        an ssh_keyfile and ssh_keyvalue specified.
        """
        url = reverse("cred-list")
        ssh_keyfile = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile.touch()
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
            "ssh_keyfile": str(ssh_keyfile),
            "ssh_keyvalue": openssh_key,
        }
        response = django_client.post(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [messages.HC_KEYFILE_OR_KEYVALUE]

    def test_hc_create_err_pwd_and_ssh_keyvalue(self, django_client, openssh_key):
        """Test API with both password and ssh_keyvalue.

        Ensure we cannot create a new host credential object with both
        a password and ssh_keyvalue specified.
        """
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "ssh_keyvalue": openssh_key,
        }
        response = django_client.post(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [
            messages.HC_PWD_NOT_WITH_KEYVALUE
        ]

    def test_hc_create_err_passphrase_and_no_keyfile_or_keyvalue(
        self, django_client, faker
    ):
        """Test API with a passphrase and no ssh_keyfile or ssh_keyvalue.

        Ensure we cannot create a new host credential object with a passphrase
        and no ssh_keyfile or ssh_keyvalue.
        """
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": faker.password(length=12),
            "ssh_passphrase": faker.password(length=16),
        }
        response = django_client.post(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_passphrase"] == [messages.HC_NO_KEY_W_PASS]

    def test_hc_create_long_name(self, django_client):
        """Test API with long name.

        Ensure we cannot create a new host credential object with a
        long name.
        """
        expected_error = {"name": ["Ensure this field has no more than 64 characters."]}
        url = reverse("cred-list")
        data = {
            "name": "A" * 100,
            "username": "user1",
            "password": "pass1",
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_long_user(self, django_client):
        """Test API with long user.

        Ensure we cannot create a new host credential object with a
        long username.
        """
        expected_error = {
            "username": ["Ensure this field has no more than 64 characters."]
        }
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "A" * 100,
            "password": "pass1",
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_long_password(self, django_client):
        """Test api with long password.

        Ensure we cannot create a new host credential object with a
        long password.
        """
        expected_error = {
            "password": ["Ensure this field has no more than 1024 characters."]
        }
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "password": "A" * 2000,
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_long_become(self, django_client):
        """Test api with long become password.

        Ensure we cannot create a new host credential object with a
        long become_password.
        """
        expected_error = {
            "become_password": ["Ensure this field has no more than 1024 characters."]
        }
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "password": "pass1",
            "become_password": "A" * 2000,
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_long_ssh(self, django_client):
        """Test api with long ssh.

        Ensure we cannot create a new host credential object with a
        long ssh_keyfile.
        """
        expected_error = {
            "ssh_keyfile": ["Ensure this field has no more than 1024 characters."]
        }
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "ssh_keyfile": "A" * 2000,
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hostcred_list_view(self, django_client):
        """Tests the list view set of the Credential API."""
        url = reverse("cred-list")
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_hostcred_list_filter_view(self, django_client):
        """Tests the list view with filter set of the Credential API."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)

        data = {
            "name": "cred2",
            "cred_type": DataSources.VCENTER,
            "username": "user2",
            "password": "pass2",
        }
        self.create_expect_201(data, django_client)

        url = reverse("cred-list")
        resp = django_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        json_resp = resp.json()
        assert json_resp.get("results") is not None
        results = json_resp.get("results")
        assert len(results) == 2

        resp = django_client.get(url, params={"cred_type": DataSources.VCENTER})
        assert resp.status_code == status.HTTP_200_OK
        json_resp = resp.json()
        assert json_resp.get("results") is not None
        results = json_resp.get("results")
        assert len(results) == 1

    def test_hostcred_update_view(self, django_client):
        """Tests the update view set of the Credential API."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)

        data = {
            "name": "cred2",
            "cred_type": DataSources.NETWORK,
            "username": "user2",
            "password": "pass2",
        }
        resp2 = self.create_expect_201(data, django_client)

        data = {"name": "cred2", "username": "user23", "password": "pass2"}
        url = reverse("cred-detail", args=(resp2["id"],))
        resp = django_client.put(url, json=data)
        assert resp.status_code == status.HTTP_200_OK

    def test_hostcred_update_double(self, django_client):
        """Update to new name that conflicts with other should fail."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)

        data = {
            "name": "cred2",
            "cred_type": DataSources.NETWORK,
            "username": "user2",
            "password": "pass2",
        }
        resp2 = self.create_expect_201(data, django_client)

        data = {"name": "cred1", "username": "user2", "password": "pass2"}
        url = reverse("cred-detail", args=(resp2["id"],))
        resp = django_client.put(url, json=data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_hostcred_get_bad_id(self, django_client):
        """Tests the get view set of the Credential API with a bad id."""
        url = reverse("cred-detail", args=("string",))
        resp = django_client.get(url, headers=ACCEPT_JSON_HEADER)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_hostcred_delete_view(self, django_client):
        """Tests the delete view set of the Credential API."""
        cred = Credential(name="cred2", username="user2", password="pass2")
        cred.save()
        url = reverse("cred-detail", args=(cred.pk,))
        resp = django_client.delete(url, headers=ACCEPT_JSON_HEADER)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_cred_delete_with_source(self, django_client):
        """Tests delete when cred used by source."""
        cred = Credential(name="cred2", username="user2", password="pass2")
        cred.save()
        source = Source(
            name="cred_source",
            source_type=DataSources.NETWORK,
            hosts=["1.2.3.4"],
        )
        source.save()
        source.credentials.add(cred)
        source.save()

        url = reverse("cred-detail", args=(cred.pk,))
        resp = django_client.delete(url, headers=ACCEPT_JSON_HEADER)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        resp_json = resp.json()
        assert resp_json["detail"] == messages.CRED_DELETE_NOT_VALID_W_SOURCES
        assert resp_json["sources"][0]["name"] == "cred_source"

    def test_vcentercred_create(self, django_client):
        """Ensure we can create a new vcenter credential."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

    def test_vc_cred_create_double(self, django_client):
        """Vcenter cred with duplicate name should fail."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

        self.create_expect_400(data, django_client)

    def test_vc_create_missing_password(self, django_client):
        """Test VCenter without password."""
        expected_error = {"password": ["This field is required."]}
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_vc_create_extra_keyfile(self, django_client):
        """Test VCenter without password."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_keyfile"]

    def test_vc_create_extra_become_pass(self, django_client):
        """Test VCenter with extra become password."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
            "become_password": "pass2",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["become_password"]

    def test_vcentercred_update(self, django_client):
        """Ensure we can create and update a vcenter credential."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"
        self.update_credential(name="cred1", username="root")
        assert Credential.objects.get().username == "root"

    def test_hostcred_default_become_method(self, django_client):
        """Ensure we can set the default become_method via API."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().become_method == "sudo"

    def test_hostcred_set_become_method(self, django_client):
        """Ensure we can set the credentials become method."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "become_method": "doas",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().become_method == "doas"

    def test_hostcred_default_become_user(self, django_client):
        """Ensure we can set the default become_user via API."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().become_user == "root"

    def test_hostcred_set_become_user(self, django_client):
        """Ensure we can set the become user."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "become_method": "doas",
            "become_user": "newuser",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().become_user == "newuser"

    def test_hostcred_set_become_pass(self, django_client):
        """Ensure we can set the become password."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "become_method": "doas",
            "become_password": "pass",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert (
            decrypt_data_as_unicode(Credential.objects.get().become_password) == "pass"
        )

    def test_vc_create_extra_keyfile_pass(self, django_client):
        """Test VCenter with extra keyfile passphase."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "password": "pass1",
            "ssh_passphrase": "pass2",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_passphrase"]

    def test_sat_cred_create(self, django_client):
        """Ensure we can create a new satellite credential."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

    def test_sat_cred_create_double(self, django_client):
        """Satellite cred with duplicate name should fail."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

        self.create_expect_400(data, django_client)

    def test_sat_create_missing_password(self, django_client):
        """Test Satellite without password."""
        expected_error = {"password": ["This field is required."]}
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_sat_cred_update_ssh_key_not_allowed(self, django_client):
        """Ensure Satellite update doesn't allow adding ssh_keyfile."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
        }
        initial = self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "cred1"

        update_data = {"name": "newName", "ssh_keyfile": "random_path"}
        url = reverse("cred-detail", args=(initial["id"],))
        response = django_client.patch(url, json=update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_keyfile"]

    def test_sat_create_extra_keyfile(self, django_client):
        """Test Satellite without password."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_keyfile"]

    def test_sat_create_extra_becomepass(self, django_client):
        """Test Satellite with extra become password."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
            "become_password": "pass2",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["become_password"]

    def test_sat_create_extra_keyfile_pass(self, django_client):
        """Test Satellite with extra keyfile passphase."""
        url = reverse("cred-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "password": "pass1",
            "ssh_passphrase": "pass2",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_passphrase"]

    def test_openshift_cred_create(self, django_client):
        """Ensure we can create a new openshift credential."""
        data = {
            "name": "openshift_cred_1",
            "cred_type": DataSources.OPENSHIFT,
            "auth_token": "test_token",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "openshift_cred_1"

    def test_openshift_missing_auth_token(self, django_client):
        """Ensure auth token is required when creating openshift credential."""
        url = reverse("cred-list")
        data = {
            "name": "openshift_cred_1",
            "cred_type": DataSources.OPENSHIFT,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [messages.TOKEN_OR_USER_PASS]

    def test_openshift_extra_unallowed_fields(self, django_client):
        """Ensure unallowed fields are not accepted when creating openshift cred."""
        url = reverse("cred-list")
        data = {
            "name": "openshift_cred_1",
            "cred_type": DataSources.OPENSHIFT,
            "auth_token": "test_token",
            "become_password": "test_become_password",
        }
        response = django_client.post(url, json=data)
        assert response.status_code, status.HTTP_400_BAD_REQUEST
        assert response.json()["become_password"]

    def test_network_ssh_keyfile_allow_none(self, django_client):
        """
        Test if sending ssh_keyfile=None don't fail validation.

        CLI is ALWAYS sending ssh_keyfile set as null [1].

        [1]: https://github.com/quipucords/qpc/blob/688d63a2350ea4ebaa20c3052d18f4d1267e1191/qpc/cred/utils.py#L83-L84
        """  # noqa: E501
        response = django_client.post(
            "/api/v1/credentials/",
            json={
                "name": "network",
                "cred_type": "network",
                "username": "some-user",
                "password": "supersecretpassword",
                "ssh_keyfile": None,
            },
        )
        assert response.ok, response.json()

    @pytest.mark.parametrize(
        "orig_type, new_type",
        (
            pytest.param(cred_type, alt_cred_type(cred_type), id=f"{cred_type}")
            for cred_type in DataSources.values
        ),
    )
    def test_hostcred_cred_type_update_fails(self, orig_type, new_type, django_client):
        """Updating a credential type to a different credential type should fail."""
        credentials = {
            "name": "cred1",
            "cred_type": orig_type,
            "username": "user1",
            "password": "pass1",
        }
        response = django_client.post(reverse("cred-list"), json=credentials)
        assert response.status_code == status.HTTP_201_CREATED

        credentials["cred_type"] = new_type
        url = reverse("cred-detail", args=(response.json()["id"],))
        resp = django_client.put(url, json=credentials)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json() == {
            "cred_type": ["cred_type is invalid for credential update"]
        }

    def test_hostcred_update_ssh_keyfile(self, tmp_path, django_client, faker):
        """Verify it is possible to change SSH key path of existing credential."""
        credential_name = "credential"
        ssh_keyfile1 = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile1.touch()
        data = {
            "name": credential_name,
            "cred_type": DataSources.NETWORK,
            "username": "some-user",
            "ssh_keyfile": str(ssh_keyfile1),
        }
        response = django_client.post(reverse("cred-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        ssh_keyfile2 = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile2.touch()
        cred_id = response.json().get("id")
        url = reverse("cred-detail", args=(cred_id,))
        data = {"name": credential_name, "ssh_keyfile": str(ssh_keyfile2)}
        response = django_client.patch(url, json=data)

        assert response.status_code == status.HTTP_200_OK
        response_ssh_keyfile = response.json().get("ssh_keyfile")
        assert response_ssh_keyfile == str(ssh_keyfile2)
        assert response_ssh_keyfile != str(ssh_keyfile1)

    def test_hostcred_update_ssh_value(
        self, django_client, faker, openssh_key, updated_openssh_key
    ):
        """Verify it is possible to change ssh_keyvalue."""
        cred_name = "cred1"
        cred_username = "user1"
        data = {
            "name": cred_name,
            "username": cred_username,
            "cred_type": DataSources.NETWORK,
            "ssh_keyvalue": openssh_key,
        }
        response = django_client.post(reverse("cred-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        cred_id = response.json()["id"]
        url = reverse("cred-detail", args=(cred_id,))
        updated_data = {
            "ssh_keyvalue": updated_openssh_key,
        }
        response = django_client.patch(url, json=updated_data)
        assert response.status_code == status.HTTP_200_OK

        cred = Credential.objects.get(id=cred_id)
        assert cred.name == cred_name
        assert cred.username == cred_username
        assert decrypt_data_as_unicode(cred.ssh_keyvalue) == updated_openssh_key

    def test_related_source_detail(self, django_client):
        """Test if related sources are included in the output."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        response = django_client.get(f"/api/v1/credentials/{credential.id}/")
        assert response.ok
        resp_data = response.json()
        assert "sources" in resp_data
        assert resp_data["sources"] == [{"id": source.id, "name": source.name}]


@pytest.mark.django_db
class TestCredentialSerialization:
    """Tests against the Credential serializer."""

    # tuple of triples (input, expected output, pytest-param-id)
    INPUT_OUTPUT_ID = (
        (
            {
                "name": "network",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "password": "some-password",
                "become_password": "become-pass",
                # this is invalid input, but OK. we're just testing serialization
                "ssh_passphrase": "non-sense",
            },
            {
                "id": mock.ANY,
                "name": "network",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "password": ENCRYPTED_DATA_MASK,
                "become_password": ENCRYPTED_DATA_MASK,
                "ssh_passphrase": ENCRYPTED_DATA_MASK,
            },
            "user-pass-become-pass",
        ),
        (
            {
                "name": "network-ssh-keyvalue",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_keyvalue": "some private SSH Keyvalue",
            },
            {
                "id": mock.ANY,
                "name": "network-ssh-keyvalue",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_keyvalue": ENCRYPTED_DATA_MASK,
            },
            "network-ssh-keyvalue",
        ),
        (
            {
                "name": "network-ssh-keyvalue-passphrase",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_keyvalue": "some private SSH Keyvalue",
                "ssh_passphrase": "some private SSH Key passphrase",
            },
            {
                "id": mock.ANY,
                "name": "network-ssh-keyvalue-passphrase",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_keyvalue": ENCRYPTED_DATA_MASK,
                "ssh_passphrase": ENCRYPTED_DATA_MASK,
            },
            "network-ssh-keyvalue-with-passphrase",
        ),
        (
            {
                "name": "satellite",
                "cred_type": DataSources.SATELLITE.value,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "satellite",
                "cred_type": DataSources.SATELLITE.value,
                "username": "some-user",
                "password": ENCRYPTED_DATA_MASK,
            },
            "satellite-user-pass",
        ),
        (
            {
                "name": "vcenter",
                "cred_type": DataSources.VCENTER.value,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "vcenter",
                "cred_type": DataSources.VCENTER.value,
                "username": "some-user",
                "password": ENCRYPTED_DATA_MASK,
            },
            "vcenter-user-pass",
        ),
        (
            {
                "name": "ocp",
                "cred_type": DataSources.OPENSHIFT.value,
                "auth_token": "token",
            },
            {
                "id": mock.ANY,
                "name": "ocp",
                "cred_type": DataSources.OPENSHIFT.value,
                "auth_token": ENCRYPTED_DATA_MASK,
            },
            "ocp-auth-token",
        ),
    )

    @pytest.mark.parametrize(
        "input_data, expected_output",
        (pytest.param(*params, id=id) for *params, id in INPUT_OUTPUT_ID),
    )
    def test_masked_data_serialization_retrieve(
        self, input_data, expected_output, django_client
    ):
        """Test if data is masked as expected for get method."""
        credential = CredentialFactory(**input_data)
        response = django_client.get(f"/api/v1/credentials/{credential.id}/")
        assert response.ok
        assert response.json() == expected_output

    def test_masked_data_serialization_list(self, django_client):
        """Test if data is masked as expected for list method."""
        results = []
        for input_data, output, _ in self.INPUT_OUTPUT_ID:
            CredentialFactory(**input_data)
            results.append(output)
        # sorting results to match default credentials api sorting
        results = sorted(results, key=lambda x: x["name"])
        response = django_client.get("/api/v1/credentials/")
        assert response.ok
        expected_output = {
            "count": len(self.INPUT_OUTPUT_ID),
            "next": None,
            "previous": None,
            "results": results,
        }
        assert response.json() == expected_output
