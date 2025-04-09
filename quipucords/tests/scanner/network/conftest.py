"""Additional pytest fixtures for testing the scanner.network package."""

import pytest

from api.credential.model import Credential
from api.source.model import Source
from constants import DataSources
from tests.factories import CredentialFactory


@pytest.mark.django_db
@pytest.fixture
def network_credential() -> Credential:
    """Return a Credential with an ssh_key."""
    return CredentialFactory(cred_type=DataSources.NETWORK, with_ssh_key=True)


@pytest.fixture
def network_host_addresses(faker) -> list[str]:
    """Return a list containing a single IPv4 host address."""
    return [faker.ipv4()]


@pytest.mark.django_db
@pytest.fixture
def network_source(
    network_credential: Credential, network_host_addresses: list[str], faker
) -> Source:
    """Return a Source with a network-type Credential for scan."""
    source = Source.objects.create(
        name="network-source-name", port=faker.pyint(), hosts=network_host_addresses
    )
    source.credentials.add(network_credential)
    return source
