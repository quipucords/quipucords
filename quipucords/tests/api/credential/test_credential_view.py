"""Test the /v2/credentials/ API views."""

import pytest
from django.urls import reverse
from rest_framework import status

from api import messages
from api.auth.hashicorp_vault.auth import HASHICORP_VAULT_NAME, HASHICORP_VAULT_TYPE
from api.secure_token.model import SecureToken
from api.vault import decrypt_data_as_unicode
from constants import DataSources
from tests.factories import CredentialFactory, SourceFactory


@pytest.fixture
def network_credential(faker):
    """Generate a network credential with fake data for tests."""
    return CredentialFactory(
        cred_type=DataSources.NETWORK,
        name=faker.name(),
        username=faker.user_name(),
        password=faker.password(),
    )


@pytest.fixture
def hashicorp_vault_config():
    """Create a global HashiCorp Vault configuration in the database."""
    return SecureToken.objects.create(
        name=HASHICORP_VAULT_NAME, token_type=HASHICORP_VAULT_TYPE
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "post_data, expected_response",
    (
        (
            {
                "name": "network-with-password-01",
                "cred_type": DataSources.NETWORK,
                "username": "username-01",
                "password": "password-01",
            },
            {
                "auth_type": "password",
                "become_method": "sudo",
                "become_user": "root",
                "cred_type": DataSources.NETWORK,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": True,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "network-with-password-01",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-01",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "network-with-password-and-become-02",
                "cred_type": DataSources.NETWORK,
                "username": "username-02",
                "password": "password-02",
                "become_user": "become-user-02",
                "become_password": "become-password-02",
            },
            {
                "auth_type": "password",
                "become_method": "sudo",
                "become_user": "become-user-02",
                "cred_type": DataSources.NETWORK,
                "has_auth_token": False,
                "has_become_password": True,
                "has_password": True,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "network-with-password-and-become-02",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-02",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "network-with-ssh-key-03",
                "cred_type": DataSources.NETWORK,
                "username": "username-03",
                "ssh_key": "ssh-key-03",
            },
            {
                "auth_type": "ssh_key",
                "become_method": "sudo",
                "become_user": "root",
                "cred_type": DataSources.NETWORK,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": False,
                "has_ssh_key": True,
                "has_ssh_passphrase": False,
                "name": "network-with-ssh-key-03",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-03",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "network-with-ssh-key-and-passphrase-04",
                "cred_type": DataSources.NETWORK,
                "username": "username-04",
                "ssh_key": "ssh-key-04",
                "ssh_passphrase": "ssh-passphrase-04",
            },
            {
                "auth_type": "ssh_key",
                "become_method": "sudo",
                "become_user": "root",
                "cred_type": DataSources.NETWORK,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": False,
                "has_ssh_key": True,
                "has_ssh_passphrase": True,
                "name": "network-with-ssh-key-and-passphrase-04",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-04",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "openshift-with-token-05",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "auth-token-05",
            },
            {
                "auth_type": "auth_token",
                "become_method": None,
                "become_user": None,
                "cred_type": DataSources.OPENSHIFT,
                "has_auth_token": True,
                "has_become_password": False,
                "has_password": False,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "openshift-with-token-05",
                "sources": [],
                "ssh_keyfile": None,
                "username": None,
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "openshift-with-password-06",
                "cred_type": DataSources.OPENSHIFT,
                "username": "username-06",
                "password": "password-06",
            },
            {
                "auth_type": "password",
                "become_method": None,
                "become_user": None,
                "cred_type": DataSources.OPENSHIFT,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": True,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "openshift-with-password-06",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-06",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "vcenter-with-password-07",
                "cred_type": DataSources.VCENTER,
                "username": "username-07",
                "password": "password-07",
            },
            {
                "auth_type": "password",
                "become_method": None,
                "become_user": None,
                "cred_type": DataSources.VCENTER,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": True,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "vcenter-with-password-07",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-07",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "ansible-with-password-08",
                "cred_type": DataSources.ANSIBLE,
                "username": "username-08",
                "password": "password-08",
            },
            {
                "auth_type": "password",
                "become_method": None,
                "become_user": None,
                "cred_type": DataSources.ANSIBLE,
                "has_auth_token": False,
                "has_become_password": False,
                "has_password": True,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "ansible-with-password-08",
                "sources": [],
                "ssh_keyfile": None,
                "username": "username-08",
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
        (
            {
                "name": "rhacs-with-token-09",
                "cred_type": DataSources.RHACS,
                "auth_token": "auth-token-09",
            },
            {
                "auth_type": "auth_token",
                "become_method": None,
                "become_user": None,
                "cred_type": DataSources.RHACS,
                "has_auth_token": True,
                "has_become_password": False,
                "has_password": False,
                "has_ssh_key": False,
                "has_ssh_passphrase": False,
                "name": "rhacs-with-token-09",
                "sources": [],
                "ssh_keyfile": None,
                "username": None,
                "vault_mount_point": None,
                "vault_secret_path": None,
                "vault_secret_key": None,
            },
        ),
    ),
)
def test_create_credential(client_logged_in, post_data: dict, expected_response: dict):
    """Test creating various types of credentials."""
    url = reverse("v2:credentials-list")
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_201_CREATED
    actual_response = response.json()
    # Because "id", "created_at", and "updated_at" are constantly changing, only
    # check that they exist, and discard them for comparing with expected values.
    assert bool(actual_response.get("id"))
    assert bool(actual_response.get("created_at"))
    assert bool(actual_response.get("updated_at"))
    del actual_response["id"]
    del actual_response["created_at"]
    del actual_response["updated_at"]
    assert actual_response == expected_response


@pytest.mark.django_db
def test_update_network_credential(client_logged_in, faker):
    """Test updating a network credential."""
    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        name=faker.name(),
        username=faker.user_name(),
        password=faker.password(),
    )
    patch_data = {
        "username": faker.user_name(),
        "password": faker.password(),
    }
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data=patch_data)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["username"] == patch_data["username"]
    credential.refresh_from_db()
    assert decrypt_data_as_unicode(credential.password) == patch_data["password"]


@pytest.mark.django_db
def test_update_openshift_credential(client_logged_in, faker):
    """Test updating an OpenShift credential."""
    credential = CredentialFactory(
        cred_type=DataSources.OPENSHIFT,
        name=faker.name(),
        username=faker.user_name(),
        password=faker.password(),
    )
    patch_data = {
        "auth_token": faker.password(),
    }
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data=patch_data)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["username"] is None
    assert not response_json["has_password"]
    assert response_json["has_auth_token"]
    credential.refresh_from_db()
    assert decrypt_data_as_unicode(credential.auth_token) == patch_data["auth_token"]


@pytest.mark.django_db
@pytest.mark.parametrize("cred_type", (DataSources.VCENTER, DataSources.ANSIBLE))
def test_update_vcenter_and_ansible_credentials(client_logged_in, faker, cred_type):
    """
    Test updating VCenter and Ansible credentials.

    These types are tested together because they generally have the same logic,
    both supporting only a simple username+password combination.
    """
    credential = CredentialFactory(
        cred_type=cred_type,
        name=faker.name(),
        username=faker.user_name(),
        password=faker.password(),
    )
    patch_data = {
        "username": faker.name(),
        "password": faker.password(),
    }
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data=patch_data)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["username"] == patch_data["username"]
    credential.refresh_from_db()
    assert decrypt_data_as_unicode(credential.password) == patch_data["password"]


@pytest.mark.django_db
def test_update_rhacs_credentials(client_logged_in, faker):
    """Test updating a RHACS credential."""
    credential = CredentialFactory(
        cred_type=DataSources.RHACS,
        name=faker.name(),
        auth_token=faker.password(),
    )
    patch_data = {
        "auth_token": faker.password(),
    }
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data=patch_data)
    assert response.status_code == status.HTTP_200_OK
    credential.refresh_from_db()
    assert decrypt_data_as_unicode(credential.auth_token) == patch_data["auth_token"]


@pytest.mark.django_db
def test_delete_unused_credential_success(network_credential, client_logged_in):
    """Test deleting an unused credential is allowed."""
    url = reverse("v2:credentials-detail", args=[network_credential.id])
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_used_credential_error(network_credential, client_logged_in):
    """Test deleting a credential that is assigned to a source returns an error."""
    SourceFactory(credentials=[network_credential])
    url = reverse("v2:credentials-detail", args=[network_credential.id])
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_delete_unknown_credential_error(faker, client_logged_in):
    """Test deleting an unknown credential ID returns an error."""
    credential_id = faker.pyint(min_value=1701)
    url = reverse("v2:credentials-detail", args=[credential_id])
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize("cred_type", (DataSources.OPENSHIFT, DataSources.ANSIBLE))
def test_create_credential_with_vault(
    client_logged_in, hashicorp_vault_config, cred_type
):
    """Test creating a credential with vault_secret_path for allowed types."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": f"vault-cred-{cred_type}",
        "cred_type": cred_type,
        "vault_secret_path": "my/secret/path",
        "vault_mount_point": "custom-mount",
        "vault_secret_key": "auth_token",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["auth_type"] == "vault_secret_path"
    assert response_json["vault_secret_path"] == "my/secret/path"
    assert response_json["vault_mount_point"] == "custom-mount"
    assert response_json["has_password"] is False
    assert response_json["has_auth_token"] is False
    assert response_json["username"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("cred_type", (DataSources.OPENSHIFT, DataSources.ANSIBLE))
def test_create_credential_with_vault_no_mount_point(
    client_logged_in, hashicorp_vault_config, cred_type
):
    """Test creating a vault credential without mount_point defaults to null."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": f"vault-cred-no-mount-{cred_type}",
        "cred_type": cred_type,
        "vault_secret_path": "my/secret/path",
        "vault_secret_key": "auth_token",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["vault_mount_point"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("cred_type", (DataSources.OPENSHIFT, DataSources.ANSIBLE))
def test_create_credential_with_vault_no_config(client_logged_in, cred_type):
    """Test creating a vault credential fails when no Vault config exists."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": f"vault-cred-no-config-{cred_type}",
        "cred_type": cred_type,
        "vault_secret_path": "my/secret/path",
        "vault_secret_key": "auth_token",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert messages.VAULT_SECRET_PATH_REQUIRES_CONFIG in str(response.json())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cred_type",
    (
        DataSources.NETWORK,
        DataSources.VCENTER,
        DataSources.SATELLITE,
        DataSources.RHACS,
    ),
)
def test_create_credential_with_vault_invalid_type(
    client_logged_in, hashicorp_vault_config, cred_type
):
    """Test creating a vault credential fails for unsupported cred types."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": f"vault-cred-invalid-{cred_type}",
        "cred_type": cred_type,
        "vault_secret_path": "my/secret/path",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_openshift_credential_with_vault_and_token(
    client_logged_in, hashicorp_vault_config
):
    """Test vault_secret_path and auth_token are mutually exclusive."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": "vault-and-token",
        "cred_type": DataSources.OPENSHIFT,
        "vault_secret_path": "my/secret/path",
        "auth_token": "some-token",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert messages.TOKEN_OR_USER_PASS_OR_VAULT_EXCLUSIVE in str(response.json())


@pytest.mark.django_db
def test_create_openshift_credential_with_vault_and_password(
    client_logged_in, hashicorp_vault_config
):
    """Test vault_secret_path and username+password are mutually exclusive."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": "vault-and-password",
        "cred_type": DataSources.OPENSHIFT,
        "vault_secret_path": "my/secret/path",
        "username": "user",
        "password": "pass",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert messages.TOKEN_OR_USER_PASS_OR_VAULT_EXCLUSIVE in str(response.json())


@pytest.mark.django_db
def test_create_ansible_credential_with_vault_and_password(
    client_logged_in, hashicorp_vault_config
):
    """Test vault + password are mutually exclusive for ansible."""
    url = reverse("v2:credentials-list")
    post_data = {
        "name": "vault-and-password-ansible",
        "cred_type": DataSources.ANSIBLE,
        "vault_secret_path": "my/secret/path",
        "username": "user",
        "password": "pass",
    }
    response = client_logged_in.post(url, data=post_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert messages.USER_PASS_OR_VAULT_NOT_BOTH in str(response.json())


@pytest.mark.django_db
def test_update_openshift_credential_to_vault(
    client_logged_in, hashicorp_vault_config, faker
):
    """Test PATCH switching an OpenShift credential from token to vault."""
    credential = CredentialFactory(
        cred_type=DataSources.OPENSHIFT,
        name=faker.name(),
        auth_token=faker.password(),
    )
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(
        url, data={"vault_secret_path": "ocp/creds", "vault_secret_key": "auth_token"}
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["auth_type"] == "vault_secret_path"
    assert response_json["vault_secret_path"] == "ocp/creds"
    assert response_json["vault_secret_key"] == "auth_token"
    assert response_json["has_auth_token"] is False
    assert response_json["has_password"] is False
    assert response_json["username"] is None


@pytest.mark.django_db
def test_update_credential_to_vault_without_vault_secret_key_rejected(
    client_logged_in, hashicorp_vault_config, faker
):
    """Test PATCH switch to vault_secret_path without vault_secret_key is rejected."""
    credential = CredentialFactory(
        cred_type=DataSources.OPENSHIFT,
        name=faker.name(),
        auth_token=faker.password(),
    )
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data={"vault_secret_path": "ocp/creds"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_ansible_credential_to_vault_without_vault_secret_key_rejected(
    client_logged_in, hashicorp_vault_config, faker
):
    """Test PATCH switching Ansible to vault without vault_secret_key is rejected."""
    credential = CredentialFactory(
        cred_type=DataSources.ANSIBLE,
        name=faker.name(),
        username=faker.user_name(),
        password=faker.password(),
    )
    url = reverse("v2:credentials-detail", args=[credential.id])
    response = client_logged_in.patch(url, data={"vault_secret_path": "ansible/creds"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_openshift_credential_from_vault(
    client_logged_in, hashicorp_vault_config, faker
):
    """Test PATCH switching an OpenShift credential from vault to token."""
    credential = CredentialFactory(
        cred_type=DataSources.OPENSHIFT,
        name=faker.name(),
        auth_token=None,
        username=None,
        password=None,
        vault_secret_path="ocp/creds",
        vault_mount_point="secret",
    )
    url = reverse("v2:credentials-detail", args=[credential.id])
    new_token = faker.password()
    response = client_logged_in.patch(url, data={"auth_token": new_token})
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["auth_type"] == "auth_token"
    assert response_json["vault_secret_path"] is None
    assert response_json["vault_mount_point"] is None
    assert response_json["has_auth_token"] is True
    credential.refresh_from_db()
    assert decrypt_data_as_unicode(credential.auth_token) == new_token
