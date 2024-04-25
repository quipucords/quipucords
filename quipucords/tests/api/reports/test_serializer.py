"""Test report serializers."""

import pytest

from api.reports.serializer import SourceSerializer
from api.serializers import ReportUploadSerializer
from constants import DataSources


@pytest.fixture
def example_source(faker):
    """Return a dict representing a valid "source"."""
    return {
        "server_id": faker.uuid4(),
        "source_name": faker.slug(),
        "source_type": faker.random_element(DataSources.values),
        "report_version": faker.bothify("%.#.##+?#?#?#?#?#?#?#"),
        "facts": [{"foo": "bar"}],
    }


@pytest.fixture
def report_missing_sources(faker):
    """Return a report payload w/o sources."""
    return {
        "report_type": "details",
        "report_platform_id": faker.uuid4(),
    }


@pytest.fixture
def report_empty_sources(faker):
    """Return a report payload with empty sources."""
    return {
        "report_type": "details",
        "report_platform_id": faker.uuid4(),
        "sources": [],
    }


@pytest.fixture
def report_invalid_report_type(faker, example_source):
    """Return a report payload with invalid report_type."""
    return {
        "report_type": "deployment",
        "report_platform_id": faker.uuid4(),
        "sources": [example_source],
    }


@pytest.fixture
def report_invalid_report_platform_id(faker, example_source):
    """Report a report payload with invalid report_platform_id."""
    return {
        "report_type": "details",
        "report_platform_id": faker.slug(),
        "sources": [example_source],
    }


@pytest.mark.parametrize(
    "data,expected_errors",
    (
        pytest.param(
            {},
            {"sources", "report_type", "report_platform_id"},
            id="missing-all",
        ),
        pytest.param(
            "report_empty_sources",
            {"sources"},
            id="empty-sources",
        ),
        pytest.param(
            "report_missing_sources",
            {"sources"},
            id="missing-sources",
        ),
        pytest.param(
            "report_invalid_report_type",
            {"report_type"},
            id="invalid-report-type",
        ),
        pytest.param(
            "report_invalid_report_platform_id",
            {"report_platform_id"},
            id="invalid-report-platform-id",
        ),
    ),
)
def test_invalid_input_for_report_upload_serializer(request, data, expected_errors):
    """Test if ReportUploadSerializer behaves as expected with invalid payloads."""
    if isinstance(data, str):
        # if data is a str, then we want the fixture with the very same name
        data = request.getfixturevalue(data)
    serializer = ReportUploadSerializer(data=data)
    assert not serializer.is_valid()
    assert expected_errors == serializer.errors.keys()


@pytest.mark.django_db
def test_valid_report_upload(faker, example_source):
    """Test 'greenpath' for ReportUploadSerializer."""
    payload = {
        "report_type": "details",
        "report_platform_id": faker.uuid4(),
        "sources": [example_source],
    }
    serializer = ReportUploadSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    report = serializer.save()
    assert str(report.report_platform_id) == payload["report_platform_id"]
    assert list(report.sources) == payload["sources"]


@pytest.fixture
def source_invalid_server_id(example_source, faker):
    """Return a dict representing a invalid "source"."""
    example_source["server_id"] = faker.slug()
    return example_source


@pytest.fixture
def source_invalid_source_type(example_source, faker):
    """Return a dict representing a invalid "source"."""
    example_source["source_type"] = faker.slug()
    return example_source


@pytest.fixture
def source_invalid_report_version(example_source, faker):
    """Return a dict representing a invalid "source"."""
    example_source["report_version"] = faker.slug()
    return example_source


@pytest.fixture
def source_report_version_missing_sha(example_source):
    """Return a dict representing a invalid "source"."""
    example_source["report_version"] = "9.9.9"
    return example_source


@pytest.fixture
def source_report_version_below_minimum_version(example_source):
    """Return a dict representing a invalid "source"."""
    example_source["report_version"] = "0.9.3+somesha"
    return example_source


@pytest.fixture
def source_empty_facts(example_source):
    """Return a dict representing a invalid "source"."""
    example_source["facts"] = []
    return example_source


@pytest.fixture
def source_missing_facts(example_source):
    """Return a dict representing a invalid "source"."""
    example_source.pop("facts")
    return example_source


@pytest.mark.parametrize(
    "data,expected_errors",
    (
        pytest.param(
            {},
            {"server_id", "source_name", "source_type", "report_version", "facts"},
            id="missing-all",
        ),
        pytest.param("source_invalid_server_id", {"server_id"}, id="invalid_server_id"),
        pytest.param(
            "source_invalid_source_type", {"source_type"}, id="invalid_source_type"
        ),
        pytest.param(
            "source_invalid_report_version",
            {"report_version"},
            id="invalid_report_version",
        ),
        pytest.param(
            "source_report_version_missing_sha",
            {"report_version"},
            id="report_version_missing_sha",
        ),
        pytest.param(
            "source_report_version_below_minimum_version",
            {"report_version"},
            id="report_version_below_minimum_version",
        ),
        pytest.param("source_empty_facts", {"facts"}, id="empty_facts"),
        pytest.param("source_missing_facts", {"facts"}, id="missing_facts"),
    ),
)
def test_invalid_input_for_source_serializer(request, data, expected_errors):
    """Test if SourceSerializer behaves as expected with invalid payloads."""
    if isinstance(data, str):
        # if data is a str, then we want the fixture with the very same name
        data = request.getfixturevalue(data)
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid()
    assert expected_errors == serializer.errors.keys()
