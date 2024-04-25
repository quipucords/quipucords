"""Test the report API."""

import json
import tarfile
from io import BytesIO

import pytest
from rest_framework.reverse import reverse

from api.models import Report
from constants import DataSources
from tests.factories import ReportFactory
from tests.utils import fake_semver


@pytest.fixture
def sources(faker):
    """Return a sources list for details report."""
    return [
        {
            "server_id": faker.uuid4(),
            "source_type": faker.random_element(DataSources.values),
            "source_name": faker.slug(),
            "report_version": f"{fake_semver()}+{faker.sha1()}",
            "facts": [{"tomato": "tomate", "potato": "batata"}],
        }
    ]


@pytest.mark.django_db
class TestDetailsReport:
    """Test details report view."""

    def test_retrieve_json(self, sources, client_logged_in):
        """Test details report view in json format (the default)."""
        report = ReportFactory(sources=sources)
        response = client_logged_in.get(
            reverse("v1:reports-details", args=(report.id,))
        )
        assert response.ok, response.text
        assert response.json() == {
            "report_id": report.id,
            "report_version": report.report_version,
            "sources": sources,
            "report_type": "details",
            "report_platform_id": str(report.report_platform_id),
        }

    def test_retrieve_gzipped_json(self, sources, client_logged_in):
        """Test details report view in gziped json format."""
        report = ReportFactory(sources=sources)
        response = client_logged_in.get(
            reverse("v1:reports-details", args=(report.id,)),
            headers={"Accept": "application/json+gzip"},
        )
        assert response.ok, response.text
        expected_filename = f"report_id_{report.id}/details.json"

        with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
            assert tarball.getnames() == [expected_filename]
            tar_info = tarball.extractfile(expected_filename)
            response_json = json.loads(tar_info.read().decode())

        assert response_json == {
            "report_id": report.id,
            "report_version": report.report_version,
            "sources": sources,
            "report_type": "details",
            "report_platform_id": str(report.report_platform_id),
        }

    def test_retrieve_csv(self, sources, client_logged_in):
        """Test details report view in csv format."""
        assert len(sources) == 1, "this test assumes sources has only one source."
        report: Report = ReportFactory(sources=sources, cached_csv=None)
        response = client_logged_in.get(
            reverse("v1:reports-details", args=(report.id,)),
            headers={"Accept": "text/csv"},
        )
        assert response.ok, response.text
        server_id = sources[0]["server_id"]
        source_name = sources[0]["source_name"]
        source_type = sources[0]["source_type"]
        expected_csv = (
            "Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n"
            f"{report.id},details,{report.report_version},{report.report_platform_id},1\r\n"
            "\r\n\r\n"
            "Source\r\n"
            "Server Identifier,Source Name,Source Type\r\n"
            f"{server_id},{source_name},{source_type}\r\n"
            "Facts\r\n"
            "potato,tomato\r\n"
            "batata,tomate\r\n"
            "\r\n\r\n"
        )
        assert response.text == expected_csv
        report.refresh_from_db()
        assert report.cached_csv == expected_csv
