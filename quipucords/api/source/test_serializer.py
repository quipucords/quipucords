"""Test source serializer."""
import pytest

from api import messages
from api.models import Credential, Source, SourceOptions
from api.source.serializer import SourceSerializer
from constants import DataSources


@pytest.fixture
def openshift_cred_id():
    """Return openshift credential."""
    openshift_credential = Credential.objects.create(
        name="openshift_cred",
        cred_type=DataSources.OPENSHIFT,
        auth_token="openshift_token",
    )
    return openshift_credential.id


@pytest.fixture
def satellite_cred_id():
    """Return satellite credential."""
    satellite_credential = Credential.objects.create(
        name="sat_cred",
        cred_type=DataSources.SATELLITE,
        username="satellite_user",
        password="satellite_password",
        become_password=None,
        ssh_keyfile=None,
    )
    return satellite_credential.id


@pytest.fixture
def openshift_source(openshift_cred_id):
    """Openshift Source."""
    source = Source.objects.create(
        name="source_saved",
        source_type=DataSources.OPENSHIFT,
        port=222,
        hosts='["1.2.3.4"]',
        options=SourceOptions.objects.create(ssl_cert_verify=True),
    )
    source.credentials.add(openshift_cred_id)
    source.save()
    return source


@pytest.mark.django_db
def test_unknown_source_type(openshift_cred_id):
    """Test if serializer is invalid when passing unknown source type."""
    data = {
        "name": "source1",
        "source_type": "test_source_type",
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "source_type" in serializer.errors


@pytest.mark.django_db
def test_wrong_cred_type(satellite_cred_id):
    """Test if serializer is invalid when passing inappropriate cred type."""
    error_message = messages.SOURCE_CRED_WRONG_TYPE
    data = {
        "name": "source2",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [satellite_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert "source_type" in serializer.errors
    assert error_message in serializer.errors["source_type"]


@pytest.mark.django_db
def test_openshift_source_green_path(openshift_cred_id):
    """Test if serializer is valid when passing mandatory fields."""
    data = {
        "name": "source3",
        "source_type": DataSources.OPENSHIFT,
        "port": 222,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    source: Source = serializer.save()
    assert source.port == 222
    assert source.hosts == '["1.2.3.4"]'
    assert source.options.ssl_cert_verify


@pytest.mark.django_db
def test_openshift_source_default_port(openshift_cred_id):
    """Test if serializer is valid when not passing port field."""
    data = {
        "name": "source3",
        "source_type": DataSources.OPENSHIFT,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["port"] == 6443


@pytest.mark.xpass("hosts ('5.4.3.2.1') is clearly invalid in this case")
@pytest.mark.django_db
def test_openshift_source_update(openshift_source, openshift_cred_id):
    """Test if serializer updates fields correctly."""
    assert openshift_source.credentials
    updated_data = {
        "name": "source_updated",
        "hosts": ["5.4.3.2.1"],
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=updated_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert openshift_source.name == "source_updated"
    assert openshift_source.source_type == DataSources.OPENSHIFT


@pytest.mark.django_db
def test_openshift_source_update_options(openshift_source, openshift_cred_id):
    """Test if serializer updates fields correctly when options are present."""
    assert openshift_source.options.ssl_cert_verify
    updated_data = {
        "name": "source_updated",
        "hosts": ["5.4.3.2"],
        "options": {"ssl_cert_verify": False},
        "credentials": [openshift_cred_id],
    }
    serializer = SourceSerializer(data=updated_data, instance=openshift_source)
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    assert openshift_source.name == "source_updated"
    assert openshift_source.source_type == DataSources.OPENSHIFT
    assert not openshift_source.options.ssl_cert_verify
