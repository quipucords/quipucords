"""Test credentials serializer."""
import pytest

from api.credential.serializer import CredentialSerializer
from api.messages import CRED_TYPE_NOT_ALLOWED_UPDATE
from api.models import Credential
from constants import DataSources
from tests.factories import CredentialFactory


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


def test_openshift_cred_unallowed_fields():
    """Test if serializer is invalid when passing unallowed fields."""
    data = {
        "name": "cred1",
        "cred_type": DataSources.OPENSHIFT,
        "auth_token": "test_auth_token",
        "password": "test_password",
        "become_password": "test_become_password",
    }
    serializer = CredentialSerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors["password"] and serializer.errors["become_password"]


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
    assert serializer.errors["cred_type"] == [CRED_TYPE_NOT_ALLOWED_UPDATE]


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
