"""
Test the deployments report API (/api/v1/reports/{id}/deployments/).

This module confirms that the CSV, JSON, and tarball (JSON inside .tar.gz) responses
from the deployments report API are structured correctly. This test does not
exhaustively test all possible fields since the shape of the outputs can change based
on the types and contents of the collected facts and system fingerprints.
"""
import csv

import pytest
from rest_framework import status

from api.common.common_report import REPORT_TYPE_DEPLOYMENT
from api.deployments_report.model import DeploymentsReport, SystemFingerprint
from api.deployments_report.util import sanitize_row
from constants import DataSources
from tests.constants import API_REPORTS_DEPLOYMENTS_PATH
from tests.factories import DeploymentReportFactory
from tests.report_utils import extract_tarball_from_response
from tests.utils import fake_semver


@pytest.fixture
def deployments_report(faker):
    """Return a DeploymentsReport for one network source with two fingerprints."""
    sources = [
        {
            "server_id": faker.uuid4(),
            "source_type": DataSources.NETWORK,
            "source_name": faker.slug(),
            "report_version": f"{fake_semver()}+{faker.sha1()}",
            "facts": [{"hello": "world", "goodnight": "moon"}],
        }
    ]
    deployments_report = DeploymentReportFactory(
        report__sources=sources, number_of_fingerprints=2
    )
    return deployments_report


def test_sanitize_row():
    """Test sanitize_row function."""
    assert sanitize_row(["data", None, "data,data"]) == ["data", None, "data;data"]


def assert_response_dict_roughly_matches_actual_fingerprint(
    system_fingerprint: SystemFingerprint, response_dict: dict
):
    """
    Spot-check a few individual values from the reported fingerprint.

    Full disclosure: These fields were picked because they are consistently populated
    by SystemFingerprintFactory that this test module uses to generate data.
    """
    assert response_dict["architecture"] == system_fingerprint.architecture
    assert response_dict["bios_uuid"] == system_fingerprint.bios_uuid
    assert response_dict["name"] == system_fingerprint.name
    assert response_dict["os_release"] == system_fingerprint.os_release
    # The following two attributes are formatted differently in CSV and JSON.
    # The CSV gets mangled string representations of list and dict objects.
    # So, simply assert truthiness if they are strings, else assert actual equality.
    if isinstance(response_dict["installed_products"], str):
        assert bool(response_dict["installed_products"]) == bool(
            system_fingerprint.installed_products
        )
    else:
        assert (
            response_dict["installed_products"] == system_fingerprint.installed_products
        )
    if isinstance(response_dict["ip_addresses"], str):
        assert bool(response_dict["ip_addresses"]) == bool(
            system_fingerprint.ip_addresses
        )
    else:
        assert response_dict["ip_addresses"] == system_fingerprint.ip_addresses


def test_get_deployments_report_as_csv(django_client, deployments_report):
    """
    Test deployments report rendering as CSV.

    This effectively tests DeploymentCSVRenderer.
    """
    response = django_client.get(
        API_REPORTS_DEPLOYMENTS_PATH.format(deployments_report.report.id),
        headers={"Accept": "text/csv"},
    )
    assert response.ok, f"response was not ok; status {response.status_code}"

    # Sanity-check the basic structure of the tarball deployments.csv directly.
    deployments_csv_data = list(csv.reader(response.text.splitlines()))
    # We expect a table header, one line in the first table, two blank lines, a section
    # marker, another table header, one line per system fingerprint in the second table,
    # and another blank line at the end. (1 + 1 + 2 + 1 + 1 + n + 1, or 7 + n)
    # Since our fixture creates two fingerprints, the total should be 9.
    # This CSV is a mess. Please put it out of its misery. >:(
    assert deployments_report.system_fingerprints.count() == 2
    assert len(deployments_csv_data) == 9

    # Directly check the CSV contents up to but not including the second table.
    expected_first_few_rows = [
        [
            "Report ID",
            "Report Type",
            "Report Version",
            "Report Platform ID",
        ],
        [
            str(deployments_report.report.id),
            REPORT_TYPE_DEPLOYMENT,
            "REPORT_VERSION",
            str(deployments_report.report_platform_id),
        ],
        [],
        [],
        ["System Fingerprints:"],
    ]
    assert (
        deployments_csv_data[: len(expected_first_few_rows)] == expected_first_few_rows
    )
    # Spot-check a couple individual values in the reported fingerprints.
    expected_first_fingerprint = deployments_report.system_fingerprints.first()
    reported_first_fingerprint = dict(
        zip(deployments_csv_data[5], deployments_csv_data[6])
    )
    assert_response_dict_roughly_matches_actual_fingerprint(
        expected_first_fingerprint, reported_first_fingerprint
    )


def test_get_deployments_report_as_json(django_client, deployments_report):
    """Test deployments report rendering as JSON."""
    response = django_client.get(
        API_REPORTS_DEPLOYMENTS_PATH.format(deployments_report.report.id),
        headers={"Accept": "application/json"},
    )
    assert response.ok, f"response was not ok; status {response.status_code}"

    deployments_json = response.json()
    deployments_json_fingerprints = deployments_json.pop("system_fingerprints")

    expected_json_without_fingerprints = {
        "report_id": deployments_report.report.id,
        "status": DeploymentsReport.STATUS_COMPLETE,
        "report_type": REPORT_TYPE_DEPLOYMENT,
        "report_version": "REPORT_VERSION",
        "report_platform_id": str(deployments_report.report_platform_id),
    }
    assert deployments_json == expected_json_without_fingerprints

    expected_fingerprints = deployments_report.system_fingerprints
    assert len(deployments_json_fingerprints) == expected_fingerprints.count()
    expected_first_fingerprint = expected_fingerprints.first()
    reported_first_fingerprint = deployments_json_fingerprints[0]
    assert_response_dict_roughly_matches_actual_fingerprint(
        expected_first_fingerprint, reported_first_fingerprint
    )


def test_get_deployment_report_as_tarball(django_client, deployments_report):
    """
    Test deployments report rendering as a JSON file inside a tarball (tar.gz).

    This effectively tests ReportJsonGzipRenderer by extracting its response and
    comparing it to the response generated from the regular JSON API.
    """
    path = API_REPORTS_DEPLOYMENTS_PATH.format(deployments_report.report.id)
    gzip_response = django_client.get(path, headers={"Accept": "application/json+gzip"})
    assert (
        gzip_response.ok
    ), f"gzip response was not ok; status {gzip_response.status_code}"
    json_response = django_client.get(path, headers={"Accept": "application/json"})
    assert (
        json_response.ok
    ), f"json response was not ok; status {json_response.status_code}"

    extracted_files = extract_tarball_from_response(gzip_response, decode_json=True)
    assert len(extracted_files) == 1
    extracted_file = list(extracted_files.values())[0]
    assert extracted_file == json_response.json()


def test_get_deployment_report_invalid_id_not_found(django_client):
    """Test getting a report for an invalid report ID responds with 404."""
    response = django_client.get(API_REPORTS_DEPLOYMENTS_PATH.format("invalid"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_deployment_report_unknown_id_not_found(django_client):
    """Test getting a report for a report ID that does not exist responds with 404."""
    response = django_client.get(API_REPORTS_DEPLOYMENTS_PATH.format("1"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_deployments_report_not_complete_424_failed(django_client):
    """Test getting a report with incomplete status responds with 424."""
    deployments_report = DeploymentReportFactory(
        number_of_fingerprints=0, status=DeploymentsReport.STATUS_PENDING
    )
    response = django_client.get(
        API_REPORTS_DEPLOYMENTS_PATH.format(deployments_report.report.id)
    )
    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY
