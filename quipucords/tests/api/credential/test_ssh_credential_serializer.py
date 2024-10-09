"""
Test SshCredentialSerializerV2.

This module tests use cases that are unique to network-type SSH credentials.
"""

import pytest

from api.credential.serializer import SshCredentialSerializerV2
from api.vault import decrypt_data_as_unicode
from constants import DataSources
from tests.factories import CredentialFactory


@pytest.mark.django_db
def test_network_credential_serializer_change_password_to_ssh_key(faker):
    """
    Test partial update clears other values when setting an SSH key.

    A credential cannot have both an SSH key and a password. So, a partial update
    containing an SSH key expects the password field to be cleared.
    """
    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        username=faker.user_name(),
        password=faker.password(),
    )
    ssh_key = faker.password()
    serializer = SshCredentialSerializerV2(
        instance=credential,
        data={"ssh_key": ssh_key},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert credential.password is None
    assert credential.ssh_key is not None
    assert decrypt_data_as_unicode(credential.ssh_key) == ssh_key
    assert not SshCredentialSerializerV2().get_has_password(credential)
    assert SshCredentialSerializerV2().get_has_ssh_key(credential)


@pytest.mark.django_db
def test_network_credential_serializer_change_ssh_key_to_password(faker):
    """
    Test partial update clears other values when setting a password.

    A credential cannot have both an SSH key and a password. So, a partial update
    containing a password expects the SSH key and SSH passphrase fields to be cleared.
    """
    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        username=faker.user_name(),
        ssh_key=faker.password(),
        ssh_passphrase=faker.password(),
    )
    password = faker.password()
    serializer = SshCredentialSerializerV2(
        instance=credential,
        data={"password": password},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert credential.ssh_key is None
    assert credential.ssh_passphrase is None
    assert credential.password is not None
    assert decrypt_data_as_unicode(credential.password) == password
    assert not SshCredentialSerializerV2().get_has_ssh_key(credential)
    assert SshCredentialSerializerV2().get_has_password(credential)


@pytest.mark.django_db
def test_network_credential_with_password_set_ssh_passphrase_invalid(faker):
    """
    Test partial update with SSH passphrase is not valid if password is set.

    This should produce an error because SSH passphrase is only relevant when
    an SSH key is also set.
    """
    credential = CredentialFactory(
        cred_type=DataSources.NETWORK,
        username=faker.user_name(),
        password=faker.password(),
    )
    serializer = SshCredentialSerializerV2(
        instance=credential,
        data={"ssh_passphrase": faker.password()},
        partial=True,
    )
    assert not serializer.is_valid()
