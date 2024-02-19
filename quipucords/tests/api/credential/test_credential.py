"""Test the API application."""
import datetime
import random
import time
from unittest import mock

import pytest
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.common.util import ids_to_str
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
    for __ in range(5):
        pkey += f"{faker.lexify('?' * 70)}\n"
    pkey += "-----END OPENSSH EXAMPLE KEY-----\n"
    return pkey


def generate_invalid_id(faker):
    """Return an invalid Credential id that will likely not exist."""
    return faker.pyint(min_value=990000, max_value=999999)


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
        url = reverse("v1:credentials-list")
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

    @pytest.mark.parametrize(
        "cred_type", (ds for ds in DataSources if ds != DataSources.RHACS)
    )
    def test_hostcred_create(self, django_client, cred_type):
        """Ensure we can create a new host credential object via API."""
        data = {
            "name": "cred1",
            "cred_type": cred_type,
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

    def test_hostcred_create_with_ssh_key(self, django_client, openssh_key):
        """Ensure we can create a new host credential object with an ssh_key."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "ssh_key": openssh_key,
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1

        cred = Credential.objects.get()
        assert cred.name == "cred1"
        assert decrypt_data_as_unicode(cred.ssh_key) == openssh_key

    def test_hostcred_create_with_ssh_key_and_passphrase(
        self, django_client, faker, openssh_key
    ):
        """Ensure we create a new credential with an ssh_key with a passphrase."""
        ssh_passphrase = faker.password(length=32)
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "ssh_key": openssh_key,
            "ssh_passphrase": ssh_passphrase,
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1

        cred = Credential.objects.get()
        assert cred.name == "cred1"
        assert decrypt_data_as_unicode(cred.ssh_key) == openssh_key
        assert decrypt_data_as_unicode(cred.ssh_passphrase) == ssh_passphrase

    def test_hostcred_create_with_unexpected_input_fields(self, django_client):
        """Creating a credential ignores unexpected or read-only fields."""
        bogus_id = int(time.time())  # arbitrarily large and unlikely integer
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "id": bogus_id,  # effectively a read-only field
            "created_at": "bogus",  # model field not in serializer
            "updated_at": "other",  # model field not in serializer
            "camelot": "it's only a model",  # completely unknown field
            "auth_token": "DEADBEEF",  # field for a different serializer
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        credential = Credential.objects.get()
        assert credential.id != bogus_id
        assert credential.name == "cred1"
        assert isinstance(credential.created_at, datetime.datetime)
        assert isinstance(credential.updated_at, datetime.datetime)
        assert not hasattr(credential, "camelot")
        # Due to current polymorphism, auth_token *exists* but should *not*
        # be set here. This is a network-type credential, and the auth_token
        # field is not used by the NetworkCredentialSerializer.
        assert not credential.auth_token

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
        cred_type = random.choice([ds for ds in DataSources])
        expected_error = {"name": ["This field is required."]}
        url = reverse("v1:credentials-list")
        data = {
            "username": "user1",
            "password": "pass1",
            "cred_type": cred_type,
        }
        if cred_type == DataSources.RHACS:
            data["auth_token"] = "auth token"
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_hc_create_err_username(self, django_client):
        """Test create without username.

        Ensure we cannot create a new host credential object without a
        username.
        """
        cred_type = random.choice(
            [ds for ds in DataSources if ds not in (DataSources.RHACS,)]
        )
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": cred_type,
            "password": "pass1",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["username"]

    def test_hc_create_err_p_or_ssh(self, django_client):
        """Test API without password, ssh_keyfile or ssh_key.

        Ensure we cannot create a new host credential object without a password,
        an ssh_keyfile, or an ssh_key.
        """
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        assert response.json()["non_field_errors"] == [
            messages.HC_PWD_OR_KEYFILE_OR_KEY
        ]

    def test_hc_create_err_ssh_bad(self, django_client):
        """Test API with bad sshkey.

        Ensure we cannot create a new host credential object an ssh_keyfile
        that cannot be found on the server.
        """
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
            "ssh_keyfile": "blah",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["ssh_keyfile"]

    def test_hc_create_err_ssh_keyfile_and_key(
        self, tmp_path, django_client, faker, openssh_key
    ):
        """Test API with both ssh_keyfile and ssh_key.

        Ensure we cannot create a new host credential object with both
        an ssh_keyfile and ssh_key specified.
        """
        url = reverse("v1:credentials-list")
        ssh_keyfile = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile.touch()
        data = {
            "name": "cred1",
            "username": "user1",
            "cred_type": DataSources.NETWORK,
            "ssh_keyfile": str(ssh_keyfile),
            "ssh_key": openssh_key,
        }
        response = django_client.post(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [messages.HC_KEYFILE_OR_KEY]

    def test_hc_create_err_pwd_and_ssh_key(self, django_client, openssh_key):
        """Test API with both password and ssh_key.

        Ensure we cannot create a new host credential object with both
        a password and ssh_key specified.
        """
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "ssh_key": openssh_key,
        }
        response = django_client.post(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [messages.HC_PWD_NOT_WITH_KEY]

    def test_hc_create_err_passphrase_and_no_keyfile_or_key(self, django_client, faker):
        """Test API with a passphrase and no ssh_keyfile or ssh_key.

        Ensure we cannot create a new host credential object with a passphrase
        and no ssh_keyfile or ssh_key.
        """
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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
        url = reverse("v1:credentials-list")
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

        url = reverse("v1:credentials-list")
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
        cred_type = random.choice(
            [ds for ds in DataSources if ds not in (DataSources.RHACS,)]
        )
        field = random.choice(["name", "username", "password"])
        data = {
            "name": "cred1",
            "cred_type": cred_type,
            "username": "user1",
            "password": "pass1",
        }
        resp = self.create_expect_201(data, django_client)

        data = {"name": "cred2", "username": "user23", "password": "pass2"}
        data[field] = "newvalue"
        url = reverse("v1:credentials-detail", args=(resp["id"],))
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
        url = reverse("v1:credentials-detail", args=(resp2["id"],))
        resp = django_client.put(url, json=data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_hostcred_retrieve_view(self, django_client):
        """Tests the get view set of the Credential API."""
        cred = Credential(name="cred2", username="user2", password="pass2")
        cred.save()
        url = reverse("v1:credentials-detail", args=(cred.pk,))
        resp = django_client.get(url, headers=ACCEPT_JSON_HEADER)
        assert resp.status_code == status.HTTP_200_OK
        json_resp = resp.json()
        assert json_resp.get("name") == "cred2"
        assert json_resp.get("username") == "user2"
        assert json_resp.get("password") == ENCRYPTED_DATA_MASK

    def test_hostcred_get_bad_id(self, django_client):
        """Tests the get view set of the Credential API with a bad id."""
        url = reverse("v1:credentials-detail", args=("string",))
        resp = django_client.get(url, headers=ACCEPT_JSON_HEADER)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_hostcred_delete_view(self, django_client):
        """Tests the delete view set of the Credential API."""
        cred = Credential(name="cred2", username="user2", password="pass2")
        cred.save()
        url = reverse("v1:credentials-detail", args=(cred.pk,))
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

        url = reverse("v1:credentials-detail", args=(cred.pk,))
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
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.VCENTER,
            "username": "user1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize(
        "cred_type", (ds for ds in DataSources if ds != DataSources.NETWORK)
    )
    @pytest.mark.parametrize("method", (m[0] for m in Credential.BECOME_METHOD_CHOICES))
    def test_create_despite_unexpected_fields(self, django_client, cred_type, method):
        """
        Test non-network source with network-specific fields like become_method.

        Because become_method and become_password only belong to network-type
        credentials, they should be ignored when saving other credential types.
        """
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": cred_type,
            "username": "user1",
            "password": "pass1",
            "become_method": method,
            "become_password": "pass2",
            "ssh_passphrase": "pass2",
            "ssh_keyfile": "/foo/bar",
        }
        if cred_type == DataSources.RHACS:
            data["auth_token"] = "auth token"
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert "become_method" not in response_json
        assert "become_password" not in response_json
        assert "ssh_keyfile" not in response_json
        assert "ssh_passphrase" not in response_json

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

    @pytest.mark.parametrize("method", (m[0] for m in Credential.BECOME_METHOD_CHOICES))
    def test_hostcred_set_become_method(self, django_client, method):
        """Ensure we can set the credentials become method."""
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "become_method": method,
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().become_method == method

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

    @pytest.mark.parametrize("method", ["not-a-method", 86])
    def test_hostcred_negative_set_become_method(self, django_client, method):
        """Test invalid become method when creating credential."""
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
            "become_method": method,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

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
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.SATELLITE,
            "username": "user1",
            "ssh_keyfile": "keyfile",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_openshift_cred_create_auth_token(self, django_client):
        """Ensure we can create a new openshift credential with auth token."""
        data = {
            "name": "openshift_cred_1",
            "cred_type": DataSources.OPENSHIFT,
            "auth_token": "test_token",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "openshift_cred_1"

    def test_openshift_cred_create_username_password(self, django_client):
        """Ensure we can create a new openshift credential with user/pass."""
        data = {
            "name": "openshift_cred_2",
            "cred_type": DataSources.OPENSHIFT,
            "username": "user1",
            "password": "pass1",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "openshift_cred_2"

    @pytest.mark.parametrize(
        "cred_type, dict_key, message",
        [
            (DataSources.RHACS, "auth_token", "This field is required."),
            (DataSources.OPENSHIFT, "non_field_errors", messages.TOKEN_OR_USER_PASS),
        ],
    )
    def test_sources_missing_required_auth_token(
        self, django_client, cred_type, dict_key, message
    ):
        """Ensure auth token is required when creating openshift/rhacs credential."""
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred_1",
            "cred_type": cred_type,
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[dict_key] == [message]

    def test_rhacs_cred_create(self, django_client):
        """Ensure we can create a new RHACS credential."""
        data = {
            "name": "acs_cred_1",
            "cred_type": DataSources.RHACS,
            "auth_token": "test_token",
        }
        self.create_expect_201(data, django_client)
        assert Credential.objects.count() == 1
        assert Credential.objects.get().name == "acs_cred_1"

    def test_network_ssh_keyfile_allow_none(self, django_client):
        """
        Test if sending ssh_keyfile=None don't fail validation.

        CLI is ALWAYS sending ssh_keyfile set as null [1].

        [1]: https://github.com/quipucords/qpc/blob/688d63a2350ea4ebaa20c3052d18f4d1267e1191/qpc/cred/utils.py#L83-L84
        """  # noqa: E501
        response = django_client.post(
            reverse("v1:credentials-list"),
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
        }
        if orig_type == DataSources.RHACS:
            credentials["auth_token"] = "test_token"
        else:
            credentials["username"] = "user1"
            credentials["password"] = "pass1"

        response = django_client.post(reverse("v1:credentials-list"), json=credentials)
        assert response.status_code == status.HTTP_201_CREATED

        credentials["cred_type"] = new_type
        url = reverse("v1:credentials-detail", args=(response.json()["id"],))
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
        response = django_client.post(reverse("v1:credentials-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        ssh_keyfile2 = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile2.touch()
        cred_id = response.json().get("id")
        url = reverse("v1:credentials-detail", args=(cred_id,))
        data = {"name": credential_name, "ssh_keyfile": str(ssh_keyfile2)}
        response = django_client.patch(url, json=data)

        assert response.status_code == status.HTTP_200_OK
        response_ssh_keyfile = response.json().get("ssh_keyfile")
        assert response_ssh_keyfile == str(ssh_keyfile2)
        assert response_ssh_keyfile != str(ssh_keyfile1)

    def test_hostcred_update_password_to_ssh_keyfile(
        self, tmp_path, django_client, faker
    ):
        """Verify credential can be changed to use SSH key instead of password."""
        credential_name = "credential"
        data = {
            "name": credential_name,
            "cred_type": DataSources.NETWORK,
            "username": "some-user",
            "password": "some-password",
        }
        response = django_client.post(reverse("v1:credentials-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        ssh_keyfile = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile.touch()
        cred_id = response.json().get("id")
        url = reverse("v1:credentials-detail", args=(cred_id,))
        data = {
            "name": credential_name,
            "password": None,
            "ssh_keyfile": str(ssh_keyfile),
        }
        response = django_client.patch(url, json=data)

        assert response.status_code == status.HTTP_200_OK
        json_resp = response.json()
        assert not json_resp.get("password")
        assert json_resp.get("ssh_keyfile") == str(ssh_keyfile)

    def test_hostcred_update_ssh_keyfile_to_password(
        self, tmp_path, django_client, faker
    ):
        """Verify credential can be changed to use password instead of SSH key."""
        credential_name = "credential"
        ssh_keyfile1 = tmp_path / faker.file_name(extension="pem")
        ssh_keyfile1.touch()
        data = {
            "name": credential_name,
            "cred_type": DataSources.NETWORK,
            "username": "some-user",
            "ssh_keyfile": str(ssh_keyfile1),
        }
        response = django_client.post(reverse("v1:credentials-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        cred_id = response.json().get("id")
        url = reverse("v1:credentials-detail", args=(cred_id,))
        data = {
            "name": credential_name,
            "password": "some-password",
            "ssh_keyfile": None,
        }
        response = django_client.patch(url, json=data)

        assert response.status_code == status.HTTP_200_OK
        json_resp = response.json()
        assert not json_resp.get("ssh_keyfile")
        assert json_resp.get("password") == ENCRYPTED_DATA_MASK

    def test_hostcred_update_ssh_value(
        self, django_client, faker, openssh_key, updated_openssh_key
    ):
        """Verify it is possible to change ssh_key."""
        cred_name = "cred1"
        cred_username = "user1"
        data = {
            "name": cred_name,
            "username": cred_username,
            "cred_type": DataSources.NETWORK,
            "ssh_key": openssh_key,
        }
        response = django_client.post(reverse("v1:credentials-list"), json=data)
        assert response.status_code == status.HTTP_201_CREATED

        cred_id = response.json()["id"]
        url = reverse("v1:credentials-detail", args=(cred_id,))
        updated_data = {
            "ssh_key": updated_openssh_key,
        }
        response = django_client.patch(url, json=updated_data)
        assert response.status_code == status.HTTP_200_OK

        cred = Credential.objects.get(id=cred_id)
        assert cred.name == cred_name
        assert cred.username == cred_username
        assert decrypt_data_as_unicode(cred.ssh_key) == updated_openssh_key

    def test_hc_update_err_pwd_and_ssh_key(self, django_client, openssh_key):
        """Test update API with both password and ssh_key.

        Ensure we cannot update a host credential object with both
        a password and ssh_key specified.
        """
        url = reverse("v1:credentials-list")
        data = {
            "name": "cred1",
            "cred_type": DataSources.NETWORK,
            "username": "user1",
            "password": "pass1",
        }
        response = django_client.post(url, json=data)
        assert response.status_code == status.HTTP_201_CREATED

        cred_id = response.json().get("id")
        url = reverse("v1:credentials-detail", args=(cred_id,))
        data.update({"ssh_key": openssh_key})
        response = django_client.patch(url, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [messages.HC_PWD_NOT_WITH_KEY]

    def test_related_source_detail(self, django_client):
        """Test if related sources are included in the output."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        response = django_client.get(
            reverse("v1:credentials-detail", args=(credential.id,))
        )
        assert response.ok
        resp_data = response.json()
        assert "sources" in resp_data
        assert resp_data["sources"] == [{"id": source.id, "name": source.name}]


@pytest.mark.django_db
class TestCredentialBulkDelete:
    """Tests the Credential bulk_delete function."""

    def test_bulk_delete_specific_ids(self, django_client):
        """Test that bulk delete deletes all requested credential IDs."""
        cred1 = CredentialFactory()
        cred2 = CredentialFactory()
        delete_request = {"ids": [cred1.id, cred2.id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.ok
        assert len(Credential.objects.filter(id__in=[cred1.id, cred2.id])) == 0

    def test_bulk_delete_all_ids(self, django_client):
        """Test that bulk delete deletes all credentials."""
        cred1 = CredentialFactory()
        cred2 = CredentialFactory()
        delete_request = {"all": True}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.ok
        assert len(Credential.objects.filter(id__in=[cred1.id, cred2.id])) == 0
        assert Credential.objects.count() == 0

    def test_bulk_delete_prefers_all_over_specific_ids(self, django_client):
        """Test that bulk delete prefers "all" over specific "ids"."""
        cred1 = CredentialFactory()
        cred2 = CredentialFactory()
        delete_request = {"all": True, "ids": [cred1.id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.ok
        assert len(Credential.objects.filter(id__in=[cred1.id, cred2.id])) == 0
        assert Credential.objects.count() == 0

    def test_bulk_delete_atomic_if_first_does_not_exist(self, django_client, faker):
        """Test bulk delete is atomic if the first credential does not exist."""
        cred1 = CredentialFactory()
        non_existent_id = generate_invalid_id(faker)
        delete_request = {"ids": [non_existent_id, cred1.id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DO_NOT_EXIST % ids_to_str([non_existent_id])
        )
        assert Credential.objects.get(pk=cred1.id).name == cred1.name

    def test_bulk_delete_atomic_if_second_does_not_exist(self, django_client, faker):
        """Test bulk deletes is atomic if the second credential does not exist."""
        cred1 = CredentialFactory()
        non_existent_id = generate_invalid_id(faker)
        delete_request = {"ids": [cred1.id, non_existent_id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DO_NOT_EXIST % ids_to_str([non_existent_id])
        )
        assert Credential.objects.get(pk=cred1.id).name == cred1.name

    def test_bulk_delete_does_not_delete_first_referenced_credential(
        self, django_client
    ):
        """Test that bulk delete does not delete first referenced credential."""
        cred1 = CredentialFactory()
        cred2 = CredentialFactory()
        SourceFactory(credentials=[cred1])
        delete_request = {"ids": [cred1.id, cred2.id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DELETE_NOT_VALID_W_SOURCES % ids_to_str([cred1.id])
        )
        assert len(Credential.objects.filter(id__in=[cred1.id, cred2.id])) == 2

    def test_bulk_delete_does_not_delete_second_referenced_credential(
        self, django_client
    ):
        """Test that bulk delete does not delete second referenced credential."""
        cred1 = CredentialFactory()
        cred2 = CredentialFactory()
        SourceFactory(credentials=[cred2])
        delete_request = {"ids": [cred1.id, cred2.id]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DELETE_NOT_VALID_W_SOURCES % ids_to_str([cred2.id])
        )
        assert len(Credential.objects.filter(id__in=[cred1.id, cred2.id])) == 2

    def test_bulk_delete_atomic_handles_multiple_credentials(self, django_client):
        """Test that bulk delete atomic operation works with multiple credentials."""
        creds = []
        for __ in range(6):
            creds.append(CredentialFactory())
        referenced_cred = creds[-1]
        SourceFactory(credentials=[referenced_cred])
        delete_request = {"ids": [cred.id for cred in creds]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DELETE_NOT_VALID_W_SOURCES
            % ids_to_str([referenced_cred.id])
        )
        assert len(
            Credential.objects.filter(id__in=[cred.id for cred in creds])
        ) == len(creds)

    def test_bulk_delete_errors_with_all_non_existent_credentials_first(
        self, django_client, faker
    ):
        """Test that bulk delete returns the 404 for all missing credentials."""
        creds = []
        for __ in range(6):
            creds.append(CredentialFactory())
        inv_cred1, inv_cred2 = generate_invalid_id(faker), generate_invalid_id(faker)
        SourceFactory(credentials=[creds[2]])
        SourceFactory(credentials=[creds[4]])
        delete_request = {"ids": [cred.id for cred in creds] + [inv_cred1, inv_cred2]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DO_NOT_EXIST % ids_to_str([inv_cred1, inv_cred2])
        )
        assert len(
            Credential.objects.filter(id__in=[cred.id for cred in creds])
        ) == len(creds)

    def test_bulk_delete_errors_with_all_credentials_with_sources(
        self, django_client, faker
    ):
        """Test that bulk delete returns the 422 for all credentials with sources."""
        creds = []
        for __ in range(6):
            creds.append(CredentialFactory())
        ref_cred1, ref_cred2 = creds[2], creds[4]
        SourceFactory(credentials=[ref_cred1])
        SourceFactory(credentials=[ref_cred2])
        delete_request = {"ids": [cred.id for cred in creds]}
        response = django_client.post(
            reverse("v1:credentials-bulk-delete"), json=delete_request
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"] == _(
            messages.CRED_IDS_DELETE_NOT_VALID_W_SOURCES
            % ids_to_str([ref_cred1.id, ref_cred2.id])
        )
        assert len(
            Credential.objects.filter(id__in=[cred.id for cred in creds])
        ) == len(creds)


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
                "name": "network-ssh-key",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_key": "some private SSH Key",
            },
            {
                "id": mock.ANY,
                "name": "network-ssh-key",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_key": ENCRYPTED_DATA_MASK,
            },
            "network-ssh-key",
        ),
        (
            {
                "name": "network-ssh-key-passphrase",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_key": "some private SSH Key",
                "ssh_passphrase": "some private SSH Key passphrase",
            },
            {
                "id": mock.ANY,
                "name": "network-ssh-key-passphrase",
                "cred_type": DataSources.NETWORK.value,
                "username": "some-user",
                "ssh_key": ENCRYPTED_DATA_MASK,
                "ssh_passphrase": ENCRYPTED_DATA_MASK,
            },
            "network-ssh-key-with-passphrase",
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
        (
            {
                "name": "ocp-user-pass",
                "cred_type": DataSources.OPENSHIFT.value,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "ocp-user-pass",
                "cred_type": DataSources.OPENSHIFT.value,
                "username": "some-user",
                "password": ENCRYPTED_DATA_MASK,
            },
            "ocp-user-pass",
        ),
        (
            {
                "name": "ansible",
                "cred_type": DataSources.ANSIBLE.value,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "ansible",
                "cred_type": DataSources.ANSIBLE.value,
                "username": "some-user",
                "password": ENCRYPTED_DATA_MASK,
            },
            "ansible",
        ),
        (
            {
                "name": "acs",
                "cred_type": DataSources.RHACS.value,
                "auth_token": "token",
            },
            {
                "id": mock.ANY,
                "name": "acs",
                "cred_type": DataSources.RHACS.value,
                "auth_token": ENCRYPTED_DATA_MASK,
            },
            "acs",
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
        response = django_client.get(
            reverse("v1:credentials-detail", args=(credential.id,))
        )
        assert response.ok
        assert response.json() == expected_output

    def test_masked_data_serialization_list(self, django_client):
        """Test if data is masked as expected for list method."""
        results = []
        for input_data, output, _id in self.INPUT_OUTPUT_ID:
            credential = CredentialFactory(**input_data)
            output["created_at"] = credential.created_at.isoformat()
            output["updated_at"] = credential.updated_at.isoformat()
            results.append(output)
        # sorting results to match default credentials api sorting
        results = sorted(results, key=lambda x: x["name"])
        response = django_client.get(reverse("v1:credentials-list"))
        assert response.ok
        expected_output = {
            "count": len(self.INPUT_OUTPUT_ID),
            "next": None,
            "previous": None,
            "results": results,
        }
        assert response.json() == expected_output
