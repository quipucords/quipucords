"""Test Source model methods."""

import pytest

from api.models import Credential, Source
from tests.factories import SourceFactory


@pytest.mark.django_db
def test_single_credential():
    """Test single_credential "green path"."""
    source: Source = SourceFactory()
    assert source.single_credential
    assert isinstance(source.single_credential, Credential)


@pytest.mark.django_db
def test_single_credential_with_multiple_credentials():
    """Test single_credential with multiple credentials."""
    source: Source = SourceFactory(number_of_credentials=10)
    with pytest.raises(Credential.MultipleObjectsReturned):
        source.single_credential


@pytest.mark.django_db
def test_single_credential_without_credential():
    """Test single_credential property when source has no credential."""
    source: Source = SourceFactory(number_of_credentials=0)
    with pytest.raises(Credential.DoesNotExist):
        source.single_credential
