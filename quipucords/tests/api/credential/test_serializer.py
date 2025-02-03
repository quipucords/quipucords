"""
Test credentials serializer.

TODO Refactor this test suite when we remove CredentialSerializerV1 and related classes.
Many tests here can be removed or simplified when we remove those older serializers.
"""

import datetime
from pathlib import Path
from unittest import mock

import pytest
from django.forms.models import model_to_dict
from rest_framework.serializers import ListSerializer

from api import messages
from api.credential.serializer import (
    AuthTokenOrUserPassSerializerV2,
    CredentialSerializerV2,
    SshCredentialSerializerV2,
    UsernamePasswordSerializerV2,
)
from api.credential.serializer_v1 import (
    AuthTokenOrUserPassSerializerV1,
    AuthTokenSerializerV1,
    CredentialSerializerV1,
    NetworkCredentialSerializerV1,
    UsernamePasswordSerializerV1,
)
from api.models import Credential
from api.vault import decrypt_data_as_unicode
from constants import ENCRYPTED_DATA_MASK, DataSources
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, CredentialSerializerV2]
)
def test_unknown_cred_type(serializer_class):
    """Test if serializer is invalid when passing unknown cred type."""
    data = {
        "name": "cred1",
        "cred_type": "test_cred_type",
        "auth_token": "test_auth_token",
    }
    serializer = serializer_class(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["cred_type"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class,input_data,expected_validated_data",
    (
        (
            CredentialSerializerV1,
            {
                "name": "cred1",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "test_auth_token",
            },
            {
                "name": "cred1",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "test_auth_token",
                "username": None,
                "password": None,
            },
        ),
        (
            AuthTokenOrUserPassSerializerV2,
            {
                "name": "cred1",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "test_auth_token",
            },
            {
                "name": "cred1",
                "cred_type": DataSources.OPENSHIFT,
                "auth_token": "test_auth_token",
                "become_method": None,
                "become_password": None,
                "become_user": None,
                "password": None,
                "ssh_key": None,
                "ssh_keyfile": None,
                "ssh_passphrase": None,
                "username": None,
            },
        ),
        (
            UsernamePasswordSerializerV2,
            {
                "name": "cred1",
                "cred_type": DataSources.ANSIBLE,
                "username": "test_username",
                "password": "test_password",
            },
            {
                "name": "cred1",
                "cred_type": DataSources.ANSIBLE,
                "auth_token": None,
                "become_method": None,
                "become_password": None,
                "become_user": None,
                "password": "test_password",
                "ssh_key": None,
                "ssh_keyfile": None,
                "ssh_passphrase": None,
                "username": "test_username",
            },
        ),
        (
            SshCredentialSerializerV2,
            {
                "name": "cred1",
                "cred_type": DataSources.NETWORK,
                "become_method": Credential.BECOME_SUDO,
                "ssh_key": "test_ssh_key",
                "ssh_passphrase": "test_ssh_passphrase",
                "username": "test_username",
            },
            {
                "name": "cred1",
                "cred_type": DataSources.NETWORK,
                "auth_token": None,
                "become_method": Credential.BECOME_SUDO,
                "become_user": Credential.BECOME_USER_DEFAULT,
                "password": None,
                "ssh_key": "test_ssh_key",
                "ssh_keyfile": None,
                "ssh_passphrase": "test_ssh_passphrase",
                "username": "test_username",
            },
        ),
    ),
)
def test_credential_serializer_is_valid_happy_path(
    serializer_class, input_data, expected_validated_data
):
    """
    Test if each serializer is valid when passing mandatory fields.

    The many `Nones` in `expected_validated_data` ensure that the serializer is
    correctly blanking-out attributes that are not relevant to this `cred_type`.
    """
    serializer = serializer_class(data=input_data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == expected_validated_data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_openshift_cred_empty_auth_token(serializer_class):
    """Test if serializer is invalid when auth token is empty."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
        "auth_token": "",
    }
    serializer = serializer_class(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["non_field_errors"] == [messages.TOKEN_OR_USER_PASS]
    # The above assertion is technically correct but maybe misleading. We allow the
    # `auth_token` field to be blank; so, technically there is no error on that field.
    # Instead, we rely on the serializer's `validate` method to identify the problem
    # and raise the non-field-error TOKEN_OR_USER_PASS.


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_openshift_cred_absent_auth_token(serializer_class):
    """Test if serializer is invalid when auth token is absent."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
    }
    serializer = serializer_class(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["non_field_errors"] == [messages.TOKEN_OR_USER_PASS]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_openshift_cred_update(serializer_class, ocp_credential):
    """Test if serializer updates fields correctly."""
    updated_data = {
        "name": "cred2",
        "auth_token": "test_auth_token",
    }
    serializer = serializer_class(
        data=updated_data, instance=ocp_credential, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert ocp_credential.name == "cred2"
    assert ocp_credential.cred_type == DataSources.OPENSHIFT


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_openshift_cred_update_no_token(serializer_class, ocp_credential):
    """Test if serializer updates fields correctly."""
    original_auth_token = decrypt_data_as_unicode(ocp_credential.auth_token)
    updated_data = {
        "name": "cred2",
    }
    serializer = serializer_class(
        data=updated_data, instance=ocp_credential, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert serializer.is_valid()
    assert ocp_credential.name == "cred2"
    assert ocp_credential.cred_type == DataSources.OPENSHIFT
    assert decrypt_data_as_unicode(ocp_credential.auth_token) == original_auth_token


@pytest.mark.xfail(reason="Missing mandatory field when updating token to user+pass")
@pytest.mark.django_db
def test_openshift_cred_update_no_password(ocp_credential):
    """Test if serializer rejects update to username without password."""
    updated_data = {
        "username": "my ocp username",
    }
    serializer = AuthTokenOrUserPassSerializerV2(
        data=updated_data, instance=ocp_credential, partial=True
    )
    assert not serializer.is_valid(), serializer.errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_openshift_update_cred_partial(serializer_class, ocp_credential):
    """Test if serializer with partial update."""
    original_auth_token = ocp_credential.auth_token
    updated_data = {
        "auth_token": "updated_test_auth_token",
    }
    serializer = serializer_class(
        data=updated_data, partial=True, instance=ocp_credential
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert ocp_credential.auth_token != original_auth_token


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_create_cred_with_non_unique_name(serializer_class):
    """Ensure it's not possible to create credentials with non-unique names."""
    CredentialFactory(
        cred_type=DataSources.OPENSHIFT, name="non-unique", auth_token="token"
    )
    serializer = serializer_class(
        data={
            "name": "non-unique",
            "cred_type": DataSources.OPENSHIFT,
            "auth_token": "other token",
        }
    )
    assert not serializer.is_valid()
    assert serializer.errors == {"name": ["credential with this name already exists."]}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, SshCredentialSerializerV2]
)
def test_change_cred_type(serializer_class):
    """Test if an attempt to change credential type will cause an error."""
    credential = CredentialFactory(cred_type=DataSources.NETWORK, name="whatever")
    serializer = serializer_class(
        data={
            "cred_type": DataSources.OPENSHIFT,
        },
        instance=credential,
        partial=True,
    )
    assert not serializer.is_valid()
    assert serializer.errors["cred_type"] == [messages.CRED_TYPE_NOT_ALLOWED_UPDATE]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer_class", [CredentialSerializerV1, AuthTokenOrUserPassSerializerV2]
)
def test_change_with_same_cred_type(serializer_class):
    """Test if "changing" a credential with the same cred_type won't raise an error."""
    credential = CredentialFactory(cred_type=DataSources.OPENSHIFT, name="whatever")
    serializer = serializer_class(
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
            value = decrypt_data_as_unicode(value)  # noqa: PLW2901
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
def test_credential_serializer_v1_creation(input_data, expected_output):
    """Test credential creation through serializer."""
    serializer = CredentialSerializerV1(data=input_data)
    assert serializer.is_valid(), serializer.errors
    credential = serializer.save()
    cred_as_dict = convert_credential_to_dict(credential)
    assert cred_as_dict == expected_output


def test_credential_serializer_v1_always_required_fields():
    """Regardless of credential type, name and cred_type fields are always required."""
    serializer = CredentialSerializerV1(data={})
    assert not serializer.is_valid()
    assert {"name", "cred_type"}.issubset(serializer.errors)


@pytest.mark.django_db
@pytest.mark.parametrize("data_source", (DataSources.VCENTER, DataSources.SATELLITE))
@pytest.mark.parametrize("extra_fields", ({"username": "user"}, {"password": "pass"}))
def test_auth_credentials(data_source, extra_fields):
    """Test auth based credentials."""
    serializer = CredentialSerializerV1(
        data={"name": "test-data", "cred_type": data_source, **extra_fields}
    )
    assert not serializer.is_valid()


@pytest.mark.django_db
class TestNetworkCredentialV1:
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
        serializer = CredentialSerializerV1(
            data={
                "name": "network-credential",
                "cred_type": DataSources.NETWORK,
                "username": "john-doe",
                "password": "shhhhhhhhhh-this-is-secret",
                "ssh_keyfile": fake_ssh_key,
            }
        )
        assert not serializer.is_valid()
        assert serializer.errors == {
            "non_field_errors": [messages.HC_PWD_NOT_WITH_KEYFILE]
        }

    def test_neither_password_or_ssh_key(self):
        """Test validation of a payload without password and ssh_key."""
        serializer = CredentialSerializerV1(
            data={
                "name": "network-credential",
                "cred_type": DataSources.NETWORK,
                "username": "john-doe",
            }
        )
        assert not serializer.is_valid()
        assert serializer.errors == {
            "non_field_errors": [messages.HC_PWD_OR_KEYFILE_OR_KEY]
        }

    def test_replace_password(self, credential_with_ssh_key):
        """Test replacing password with ssh_keyfile."""
        serializer = CredentialSerializerV1(
            data={
                "password": "super-duper-secret",
            },
            instance=credential_with_ssh_key,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert (
            decrypt_data_as_unicode(credential_with_ssh_key.password)
            == "super-duper-secret"
        )
        assert credential_with_ssh_key.ssh_keyfile is None, (
            "the same credential can't have both ssh_keyfile and password"
        )

    def test_replace_ssh_keyfile(self, credential_with_password, fake_ssh_key):
        """Test replacing ssh_keyfile with password."""
        serializer = CredentialSerializerV1(
            data={
                "ssh_keyfile": fake_ssh_key,
            },
            instance=credential_with_password,
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert credential_with_password.password is None, (
            "the same credential can't have both ssh_keyfile and password"
        )
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
        serializer = CredentialSerializerV1(
            data=payload_with_passphrase_without_ssh_key,
        )
        assert not serializer.is_valid()
        assert serializer.errors == {"ssh_passphrase": [messages.HC_NO_KEY_W_PASS]}

    @pytest.mark.parametrize(
        "kwargs",
        (
            pytest.param({}, id="full-update"),
            pytest.param({"partial": True}, id="partial-update"),
        ),
    )
    def test_update_ssh_passphrase_without_ssh_keyfile(
        self,
        payload_with_passphrase_without_ssh_key,
        kwargs,
        credential_with_password,
    ):
        """Test updating a credential with ssh_passphrase and w/o ssh key."""
        serializer = CredentialSerializerV1(
            data=payload_with_passphrase_without_ssh_key,
            instance=credential_with_password,
            **kwargs,
        )
        assert not serializer.is_valid(), "ssh_passphrase require a ssh_key!"
        assert serializer.errors == {"ssh_passphrase": [messages.HC_NO_KEY_W_PASS]}

    def test_only_partial_update_ssh_passphrase_with_previously_saved_ssh_key(
        self,
        payload_with_passphrase_without_ssh_key: dict,
        credential_with_ssh_key: Credential,
    ):
        """Test partial update of ssh_passphrase with saved ssh_key."""
        serializer = CredentialSerializerV1(
            data=payload_with_passphrase_without_ssh_key,
            instance=credential_with_ssh_key,
            partial=True,
        )
        assert serializer.is_valid()
        assert not credential_with_ssh_key.ssh_passphrase
        serializer.save()
        assert credential_with_ssh_key.ssh_passphrase


@pytest.mark.parametrize(
    "cred_type, base_class, expected_class",
    (
        (DataSources.NETWORK, CredentialSerializerV1, NetworkCredentialSerializerV1),
        (
            DataSources.OPENSHIFT,
            CredentialSerializerV1,
            AuthTokenOrUserPassSerializerV1,
        ),
        (DataSources.SATELLITE, CredentialSerializerV1, UsernamePasswordSerializerV1),
        (DataSources.VCENTER, CredentialSerializerV1, UsernamePasswordSerializerV1),
        (DataSources.ANSIBLE, CredentialSerializerV1, UsernamePasswordSerializerV1),
        (DataSources.RHACS, CredentialSerializerV1, AuthTokenSerializerV1),
        # Note that all CredentialSerializerV2 bases also return CredentialSerializerV2.
        (DataSources.NETWORK, CredentialSerializerV2, CredentialSerializerV2),
        (DataSources.OPENSHIFT, CredentialSerializerV2, CredentialSerializerV2),
        (DataSources.SATELLITE, CredentialSerializerV2, CredentialSerializerV2),
        (DataSources.VCENTER, CredentialSerializerV2, CredentialSerializerV2),
        (DataSources.ANSIBLE, CredentialSerializerV2, CredentialSerializerV2),
        (DataSources.RHACS, CredentialSerializerV2, CredentialSerializerV2),
    ),
)
class TestSerializerPolymorphism:
    """
    Test serializer polymorphism.

    Note: This test is only useful for the old v1 classes. Newer v2 classes do support
    the same polymorphic instantiation and simply return an instance of the same class.

    TODO Remove this test when we remove CredentialSerializerV1.
    """

    def test_with_data(self, cred_type, base_class, expected_class):
        """Test polymorphism passing data."""
        serializer = base_class(data={"cred_type": cred_type})
        assert isinstance(serializer, expected_class)

    @pytest.mark.django_db
    def test_with_instance(self, cred_type, base_class, expected_class):
        """Test polymorphism passing instance."""
        serializer = base_class(CredentialFactory(name="cred", cred_type=cred_type))
        assert isinstance(serializer, expected_class)


class TestCredentialSerializerV1:
    """
    Test CredentialSerializerV1.

    Note: This test is only useful for the old v1 classes.
    Newer v2 classes do support the same polymorphic instantiation.

    TODO Remove this test when we remove CredentialSerializerV1.
    """

    @pytest.mark.parametrize("kwargs", ({}, {"instance": None}, {"data": {}}))
    def test_read_only_polymorphism(self, kwargs):
        """Test read_only polymorphism."""
        serializer = CredentialSerializerV1(**kwargs)
        # isinstance wouldn't be good for testing since the other classes
        # are subclasses of this one
        assert serializer.__class__ == CredentialSerializerV1

    @pytest.mark.django_db
    def test_with_multiple_instances(self):
        """Test init CredentialSerializer with many instances and many=False."""
        credentials = CredentialFactory.create_batch(10)
        serializer = CredentialSerializerV1(instance=credentials)
        # this might seem a fluke, but it's DRF design
        assert serializer.__class__ == CredentialSerializerV1
        # attempting to serialize this data would fail horribly due to lack of
        # many=True.

    @pytest.mark.django_db
    def test_with_many(self):
        """Test to serialize instances and many=True."""

        def _value_formatter(value):
            if isinstance(value, str) and Credential.is_encrypted(value):
                return ENCRYPTED_DATA_MASK
            elif isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            return value

        credentials = CredentialFactory.create_batch(10)
        serializer = CredentialSerializerV1(instance=credentials, many=True)
        assert isinstance(serializer, ListSerializer)
        assert serializer.child.__class__ == CredentialSerializerV1
        for cred_data in serializer.data:
            assert "created_at" in cred_data
            assert "updated_at" in cred_data
            assert "auth_type" in cred_data
            assert cred_data["created_at"] is not None
            assert cred_data["updated_at"] is not None
            assert cred_data["auth_type"] is not None

        expected_data = []
        # prep a list of credentials dict as the serializer would return
        for cred in credentials:
            cred_dict = {
                k: _value_formatter(v)
                for k, v in model_to_dict(cred).items()
                if v is not None
            }
            cred_dict["created_at"] = _value_formatter(cred.created_at)
            cred_dict["updated_at"] = _value_formatter(cred.updated_at)
            # auth_type is a read-only serializer field, not on the model
            cred_dict["auth_type"] = CredentialSerializerV1().get_auth_type(cred)
            expected_data.append(cred_dict)
        assert serializer.data == expected_data


class TestOCPSerializer:
    """Test serializers for OpenShift-type Credentials."""

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "serializer_class", (CredentialSerializerV1, AuthTokenOrUserPassSerializerV2)
    )
    def test_from_authtoken_to_userpass(self, serializer_class):
        """Test updating an OpenShift auth token credential to username+password."""
        credential = CredentialFactory(
            cred_type=DataSources.OPENSHIFT,
            auth_token="<TOKEN>",
        )
        serializer = serializer_class(
            instance=credential,
            data={"username": "<USER>", "password": "<PASS>"},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        assert credential.auth_token is None
        assert credential.username == "<USER>"
        assert decrypt_data_as_unicode(credential.password) == "<PASS>"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "serializer_class", (CredentialSerializerV1, AuthTokenOrUserPassSerializerV2)
    )
    def test_from_userpass_to_authtoken(self, serializer_class, faker):
        """Test updating an OpenShift username+password credential to auth token."""
        credential = CredentialFactory(
            cred_type=DataSources.OPENSHIFT,
            username=faker.user_name(),
            password=faker.password(),
        )
        serializer = serializer_class(
            instance=credential,
            data={"auth_token": "<TOKEN>"},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        assert credential.username is None
        assert credential.password is None
        assert decrypt_data_as_unicode(credential.auth_token) == "<TOKEN>"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "serializer_class", (CredentialSerializerV1, AuthTokenOrUserPassSerializerV2)
    )
    def test_no_auth(self, serializer_class, faker):
        """Test error when no auth is provided."""
        serializer = serializer_class(
            data={"cred_type": DataSources.OPENSHIFT, "name": faker.slug()}
        )
        assert not serializer.is_valid()
        assert serializer.errors["non_field_errors"] == [messages.TOKEN_OR_USER_PASS]

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "serializer_class", (CredentialSerializerV1, AuthTokenOrUserPassSerializerV2)
    )
    def test_all_auth(self, serializer_class, faker):
        """Test error when both auth methods are provided."""
        serializer = serializer_class(
            data={
                "cred_type": DataSources.OPENSHIFT,
                "name": faker.slug(),
                "auth_token": faker.md5(),
                "username": faker.user_name(),
                "password": faker.password(),
            }
        )
        assert not serializer.is_valid()
        assert serializer.errors["non_field_errors"] == [
            messages.TOKEN_OR_USER_PASS_NOT_BOTH
        ]


@pytest.mark.django_db
def test_credential_secrets_preserve_surrounding_whitespace(faker):
    """
    Test fields with "secret" encrypted values preserve original whitespace.

    Unlike other fields, it's important to preserve whitespace in fields like
    password and ssh_passphrase because leading and trailing spaces are valid,
    albeit uncommon, and must be preserved.

    Although this test only exercises SshCredentialSerializerV2, the same logic
    applies to encrypted fields in all *SerializerV2 classes. Since the fields'
    definitions are set on the parent CredentialSerializerV2 class, though, we
    do not need to test all child classes exhaustively.
    """
    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        username=faker.user_name(),
        password=faker.password(),
    )
    password_with_spaces = f"  {faker.password()}  "

    serializer = SshCredentialSerializerV2(
        instance=credential,
        data={"password": password_with_spaces},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert decrypt_data_as_unicode(credential.password) == password_with_spaces
    assert credential.ssh_key is None
    assert credential.ssh_passphrase is None

    serializer = SshCredentialSerializerV2(
        instance=credential,
        data={
            "ssh_key": password_with_spaces,
            "ssh_passphrase": password_with_spaces,
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert credential.password is None
    assert decrypt_data_as_unicode(credential.ssh_key) == password_with_spaces
    assert decrypt_data_as_unicode(credential.ssh_passphrase) == password_with_spaces


@pytest.mark.django_db
@pytest.mark.parametrize(
    "credential_type,serializer_class",
    (
        (DataSources.OPENSHIFT, AuthTokenOrUserPassSerializerV2),
        (DataSources.NETWORK, SshCredentialSerializerV2),
        (DataSources.ANSIBLE, UsernamePasswordSerializerV2),
    ),
)
def test_credential_set_name_to_empty(faker, credential_type, serializer_class):
    """Ensure you can't clear mandatory "name" field when editing credential."""
    credential = CredentialFactory(
        cred_type=credential_type,
        username=faker.user_name(),
        password=faker.password(),
    )
    serializer = serializer_class(
        instance=credential,
        data={"name": ""},
        partial=True,
    )
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["name"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "credential_type,serializer_class",
    (
        (DataSources.OPENSHIFT, AuthTokenOrUserPassSerializerV2),
        (DataSources.NETWORK, SshCredentialSerializerV2),
        (DataSources.ANSIBLE, UsernamePasswordSerializerV2),
    ),
)
def test_credential_set_username_to_empty(faker, credential_type, serializer_class):
    """Ensure you can't clear mandatory "username" field when editing credential."""
    credential = CredentialFactory(
        cred_type=credential_type,
        username=faker.user_name(),
        password=faker.password(),
    )
    serializer = serializer_class(
        instance=credential,
        data={"username": ""},
        partial=True,
    )
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["username"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "credential_type,serializer_class",
    (
        (DataSources.OPENSHIFT, AuthTokenOrUserPassSerializerV2),
        pytest.param(
            DataSources.NETWORK,
            SshCredentialSerializerV2,
            marks=pytest.mark.xfail(
                reason=(
                    "Server incorrectly allows to set mandatory password field to "
                    "empty string; see DSC-860"
                )
            ),
        ),
        (DataSources.ANSIBLE, UsernamePasswordSerializerV2),
    ),
)
def test_credential_set_password_to_empty(faker, credential_type, serializer_class):
    """Ensure you can't clear mandatory "password" field when editing credential."""
    credential = CredentialFactory(
        cred_type=credential_type,
        username=faker.user_name(),
        password=faker.password(),
    )
    serializer = serializer_class(
        instance=credential,
        data={"password": ""},
        partial=True,
    )
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["password"]
