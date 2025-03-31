"""Additional pytest fixtures for testing the scanner.network package."""

import pytest

from api.credential.model import Credential
from api.source.model import Source
from constants import DataSources
from tests.factories import generate_openssh_pkey


@pytest.fixture
def openssh_key() -> str:
    """Return an openssh_key random OpenSSH private key."""
    return generate_openssh_pkey()


@pytest.mark.django_db
@pytest.fixture
def network_credential(openssh_key: str, faker) -> Credential:
    """Return a Credential with an ssh_key."""
    return Credential.objects.create(
        name="network-credential-name",
        username="network-credential-username",
        become_method=faker.random_element(Credential.BECOME_METHOD_CHOICES)[0],
        become_password=faker.password(),
        become_user=faker.slug(),
        cred_type=DataSources.NETWORK,
        password=faker.password(),
        ssh_key=openssh_key,
    )


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
