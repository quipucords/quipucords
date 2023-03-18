"""Test credentials serializer."""
from pathlib import Path
from unittest import mock

import pytest
from django.forms.models import model_to_dict
from rest_framework.serializers import ValidationError

from api import messages
from api.credential.serializer import CredentialSerializer
from api.models import Credential
from api.vault import decrypt_data_as_unicode
from constants import DataSources
from tests.factories import CredentialFactory


@pytest.fixture
def fake_ssh_key(tmp_path: Path):
    """fake ssh key."""
    file_path = tmp_path / "ssh-key.pem"
    file_path.touch()
    yield str(file_path)


@pytest.fixture
def ocp_credential():
    """Previously created OCP Credential."""
    cred = Credential(
        name="cred1",
        cred_type=DataSources.OPENSHIFT,
        auth_token="test_auth_token",
    )
    cred.save()
    return cred


def test_unknown_cred_type():
    """Test if serializer is invalid when passing unknown cred type."""
    data = {
        "name": "cred1",
        "cred_type": "test_cred_type",
        "auth_token": "test_auth_token",
    }
    serializer = CredentialSerializer(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["cred_type"]


def test_openshift_cred_correct_fields():
    """Test if serializer is valid when passing mandatory fields."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
        "auth_token": "test_auth_token",
    }
    serializer = CredentialSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == data


@pytest.mark.parametrize(
    "input_data,improper_fields",
    (
        pytest.param(
            {
                "name": "cred",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "test_auth_token",
                "password": "test_password",
                "become_password": "test_become_password",
            },
            {"password", "become_password"},
            id="1",
        ),
        pytest.param(
            {
                "name": "cred",
                "cred_type": DataSources.NETWORK,
                "auth_token": "test_auth_token",
                "password": "test_password",
                "username": "some-user",
            },
            {"auth_token"},
            id="2",
        ),
        pytest.param(
            {
                "name": "cred",
                "cred_type": DataSources.VCENTER,
                "auth_token": "test_auth_token",
                "password": "test_password",
                "username": "some-user",
                "become_password": "test_become_password",
            },
            {"auth_token", "become_password"},
            id="3",
        ),
    ),
)
def test_openshift_cred_unallowed_fields(input_data, improper_fields):
    """Test if serializer is invalid when passing unallowed fields."""
    serializer = CredentialSerializer(data=input_data)
    assert not serializer.is_valid()
    assert improper_fields == set(serializer.errors.keys())


def test_openshift_cred_empty_auth_token():
    """Test if serializer is invalid when auth token is empty."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
        "auth_token": "",
    }
    serializer = CredentialSerializer(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["auth_token"]


def test_openshift_cred_absent_auth_token():
    """Test if serializer is invalid when auth token is absent."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
    }
    serializer = CredentialSerializer(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["auth_token"]


@pytest.mark.django_db
def test_openshift_cred_update(ocp_credential):
    """Test if serializer updates fields correctly."""
    updated_data = {
        "name": "cred2",
        "auth_token": "test_auth_token",
    }
    serializer = CredentialSerializer(data=updated_data, instance=ocp_credential)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert ocp_credential.name == "cred2"
    assert ocp_credential.cred_type == DataSources.OPENSHIFT


@pytest.mark.django_db
def test_openshift_cred_update_no_token(ocp_credential):
    """Test if serializer updates fields correctly."""
    original_auth_token = ocp_credential.auth_token
    updated_data = {
        "name": "cred2",
    }
    serializer = CredentialSerializer(data=updated_data, instance=ocp_credential)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert serializer.is_valid()
    assert ocp_credential.name == "cred2"
    assert ocp_credential.cred_type == DataSources.OPENSHIFT
    assert ocp_credential.auth_token == original_auth_token


@pytest.mark.django_db
def test_openshift_update_cred_partial(ocp_credential):
    """Test if serializer with partial update."""
    original_auth_token = ocp_credential.auth_token
    updated_data = {
        "auth_token": "updated_test_auth_token",
    }
    serializer = CredentialSerializer(
        data=updated_data, partial=True, instance=ocp_credential
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert ocp_credential.auth_token != original_auth_token


@pytest.mark.django_db
def test_create_cred_with_non_unique_name():
    """Ensure it's not possible to create credentials with non-unique names."""
    CredentialFactory(
        cred_type=DataSources.OPENSHIFT, name="non-unique", auth_token="token"
    )
    serializer = CredentialSerializer(
        data={
            "name": "non-unique",
            "cred_type": DataSources.OPENSHIFT,
            "auth_token": "other token",
        }
    )
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(ValidationError) as exc_info:
        serializer.save()
    assert exc_info.value.args[0] == {
        "name": [messages.HC_NAME_ALREADY_EXISTS % "non-unique"]
    }


@pytest.mark.django_db
def test_change_cred_type():
    """Test if an attempt to change credential type will cause an error."""
    credential = CredentialFactory(cred_type=DataSources.NETWORK, name="whatever")
    serializer = CredentialSerializer(
        data={
            "cred_type": DataSources.OPENSHIFT,
        },
        instance=credential,
        partial=True,
    )
    assert not serializer.is_valid()
    assert serializer.errors["cred_type"] == [messages.CRED_TYPE_NOT_ALLOWED_UPDATE]


@pytest.mark.django_db
def test_change_with_same_cred_type():
    """Test if "changing" a credential with the same cred_type won't raise an error."""
    credential = CredentialFactory(cred_type=DataSources.OPENSHIFT, name="whatever")
    serializer = CredentialSerializer(
        data={"cred_type": DataSources.OPENSHIFT},
        instance=credential,
        partial=True,
    )
    assert serializer.is_valid()


def convert_credential_to_dict(credential: Credential):
    """Convert Credential instance to dict."""
    cred_as_dict = {}
    for key, value in model_to_dict(credential).items():
        # skip null values (same thing CredentialSerializer does)
        if value is None:
            continue
        # decrypt data to allow easy comparison between stored data vs expected
        if isinstance(value, str) and value.startswith("$ANSIBLE_VAULT"):
            value = decrypt_data_as_unicode(value)
        cred_as_dict[key] = value
    return cred_as_dict


@pytest.fixture
def ssh_key_payload(fake_ssh_key):
    """
    Fixture representing a payload for credential creation.

    This is the minimum payload for the creation of a network scan credential using
    ssh_keyfile.
    """
    yield {
        "name": "network",
        "cred_type": DataSources.NETWORK,
        "username": "some-user",
        "ssh_keyfile": fake_ssh_key,
    }


@pytest.fixture
def ssh_key_expected_output(fake_ssh_key):
    """Fixture representing a credential for network scan using ssh_keyfile."""
    yield {
        "id": mock.ANY,
        "name": "network",
        "cred_type": DataSources.NETWORK,
        "username": "some-user",
        "ssh_keyfile": fake_ssh_key,
        "become_method": "sudo",
        "become_user": "root",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_data, expected_output",
    (
        pytest.param(
            {
                "name": "network",
                "cred_type": DataSources.NETWORK,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "network",
                "cred_type": DataSources.NETWORK,
                "username": "some-user",
                "password": "some-password",
                "become_method": "sudo",
                "become_user": "root",
            },
            id="network-user-pass",
        ),
        pytest.param(
            pytest.lazy_fixture("ssh_key_payload"),
            pytest.lazy_fixture("ssh_key_expected_output"),
            id="network-ssh-keyfile",
        ),
        pytest.param(
            {
                "name": "satellite",
                "cred_type": DataSources.SATELLITE,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "satellite",
                "cred_type": DataSources.SATELLITE,
                "username": "some-user",
                "password": "some-password",
            },
            id="satellite-user-pass",
        ),
        pytest.param(
            {
                "name": "vcenter",
                "cred_type": DataSources.VCENTER,
                "username": "some-user",
                "password": "some-password",
            },
            {
                "id": mock.ANY,
                "name": "vcenter",
                "cred_type": DataSources.VCENTER,
                "username": "some-user",
                "password": "some-password",
            },
            id="vcenter-user-pass",
        ),
        pytest.param(
            {
                "name": "ocp",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "token",
            },
            {
                "id": mock.ANY,
                "name": "ocp",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "token",
            },
            id="ocp-auth-token",
        ),
    ),
)
def test_credential_creation(input_data, expected_output):
    """Test credential creation through serializer."""
    serializer = CredentialSerializer(data=input_data)
    assert serializer.is_valid(), serializer.errors
    credential = serializer.save()
    cred_as_dict = convert_credential_to_dict(credential)
    assert cred_as_dict == expected_output


def test_always_required_fields():
    """Regardless of credential type, name and cred_type fields are always required."""
    serializer = CredentialSerializer(data={})
    assert not serializer.is_valid()
    assert {"name", "cred_type"}.issubset(serializer.errors)


@pytest.mark.parametrize("data_source", (DataSources.VCENTER, DataSources.SATELLITE))
@pytest.mark.parametrize("extra_fields", ({"username": "user"}, {"password": "pass"}))
def test_auth_credentials(data_source, extra_fields):
    """Test auth based credentials."""
    serializer = CredentialSerializer(
        data={"name": "test-data", "cred_type": data_source, **extra_fields}
    )
    assert not serializer.is_valid()


class TestNetworkCredential:
    """Group tests for network credentials."""

    @pytest.fixture
    def credential_with_ssh_key(self, fake_ssh_key):
        """Return a bare-minimum credential with ssh-key."""
        return CredentialFactory(
            cred_type=DataSources.NETWORK,
            ssh_keyfile=fake_ssh_key,
            username="john-doe",
        )

    @pytest.fixture
    def credential_with_password(self):
        """Return a bare-minimum credential with username+password."""
        return CredentialFactory(
            username="john-doe",
            cred_type=DataSources.NETWORK.value,
            password="shhhhhhhhhh-this-is-secret",
        )

    def test_both_password_and_ssh_key(self, fake_ssh_key):
        """Test validation of a payload including password and ssh_key."""
        serializer = CredentialSerializer(
            data={
                "name": "network-credential",
                "cred_type": DataSources.NETWORK,
                "username": "john-doe",
                "password": "shhhhhhhhhh-this-is-secret",
                "ssh_keyfile": fake_ssh_key,
            }
        )
        assert not serializer.is_valid()
        assert serializer.errors == {"non_field_errors": [messages.HC_NOT_BOTH]}

    def test_neither_password_or_ssh_key(self):
        """Test validation of a payload without password and ssh_key."""
        serializer = CredentialSerializer(
            data={
                "name": "network-credential",
                "cred_type": DataSources.NETWORK,
                "username": "john-doe",
            }
        )
        assert not serializer.is_valid()
        assert serializer.errors == {"non_field_errors": [messages.HC_PWD_OR_KEYFILE]}

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="This behavior is not implemented yet - clients are forced to do it."
    )
    def test_replace_password(self, credential_with_ssh_key):
        """Test replacing password with ssh_keyfile."""
        serializer = CredentialSerializer(
            data={
                "password": "super-duper-secret",
            },
            instance=credential_with_ssh_key,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert (
            decrypt_data_as_unicode(credential_with_ssh_key.password)
            == "super-duper-secret"
        )
        assert credential_with_ssh_key.ssh_keyfile is None

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="This behavior is not implemented yet - clients are forced to do it."
    )
    def test_replace_ssh_keyfile(self, credential_with_password, fake_ssh_key):
        """Test replacing ssh_keyfile with password."""
        serializer = CredentialSerializer(
            data={
                "ssh_keyfile": fake_ssh_key,
            },
            instance=credential_with_password,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert credential_with_password.password is None
        assert credential_with_password.ssh_keyfile == fake_ssh_key

    @pytest.fixture(scope="class")
    def payload_with_passphrase_without_ssh_key(self):
        """Return a payload with passphrase and without ssh key."""
        return {
            "name": "network-credential",
            "cred_type": DataSources.NETWORK,
            "username": "john-doe",
            "password": "shhhhhhhhhh-this-is-secret",
            "ssh_passphrase": "another-secret",
        }

    def test_create_ssh_passphrase_without_ssh_keyfile(
        self, payload_with_passphrase_without_ssh_key
    ):
        """Test using ssh_passphrase without a ssh key."""
        serializer = CredentialSerializer(
            data=payload_with_passphrase_without_ssh_key,
        )
        assert not serializer.is_valid()
        assert serializer.errors == {"ssh_passphrase": [messages.HC_NO_KEY_W_PASS]}

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "extra_serializer_kwargs",
        (
            pytest.param({}, id="full-update"),
            pytest.param(
                {"partial": True},
                marks=pytest.mark.xfail(reason="BUG DETECTED!"),
                id="partial-update",
            ),
        ),
    )
    def test_update_ssh_passphrase_without_ssh_keyfile(
        self,
        payload_with_passphrase_without_ssh_key,
        extra_serializer_kwargs,
        credential_with_password,
    ):
        """Test updating a credential with ssh_passphrase and w/o ssh key."""
        serializer = CredentialSerializer(
            data=payload_with_passphrase_without_ssh_key,
            instance=credential_with_password,
            **extra_serializer_kwargs,
        )
        assert not serializer.is_valid()
        assert serializer.errors == {"ssh_passphrase": [messages.HC_NO_KEY_W_PASS]}

    @pytest.mark.django_db
    def test_only_partial_update_ssh_passphrase_with_previously_saved_ssh_key(
        self,
        payload_with_passphrase_without_ssh_key: dict,
        credential_with_ssh_key: Credential,
    ):
        """Test partial update of ssh_passphrase with saved ssh_key."""
        serializer = CredentialSerializer(
            data=payload_with_passphrase_without_ssh_key,
            instance=credential_with_ssh_key,
            partial=True,
        )
        assert serializer.is_valid()
        assert not credential_with_ssh_key.ssh_passphrase
        serializer.save()
        assert credential_with_ssh_key.ssh_passphrase
