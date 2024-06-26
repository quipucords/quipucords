"""
Test the deployments report API (/api/v1/reports/{id}/deployments/).

This module confirms that the CSV, JSON, and tarball (JSON inside .tar.gz) responses
from the deployments report API are structured correctly. This test does not
exhaustively test all possible fields since the shape of the outputs can change based
on the types and contents of the collected facts and system fingerprints.
"""

import csv
import logging

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.common.common_report import REPORT_TYPE_DEPLOYMENT
from api.deployments_report.model import (
    DeploymentsReport,
    SystemFingerprint,
    cached_files_path,
)
from api.deployments_report.model import (
    time as time_module,
)
from api.deployments_report.util import sanitize_row
from constants import DataSources
from tests.factories import DeploymentReportFactory
from tests.report_utils import extract_files_from_tarball
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


@pytest.mark.django_db
def test_get_deployments_report_as_csv(client_logged_in, deployments_report):
    """
    Test deployments report rendering as CSV.

    This effectively tests DeploymentCSVRenderer.
    """
    response = client_logged_in.get(
        reverse("v1:reports-deployments", args=(deployments_report.report.id,)),
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


@pytest.mark.django_db
def test_get_deployments_report_as_json(client_logged_in, deployments_report):
    """Test deployments report rendering as JSON."""
    response = client_logged_in.get(
        reverse("v1:reports-deployments", args=(deployments_report.report.id,)),
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


@pytest.mark.django_db
def test_get_deployment_report_as_tarball(client_logged_in, deployments_report):
    """
    Test deployments report rendering as a JSON file inside a tarball (tar.gz).

    This effectively tests ReportJsonGzipRenderer by extracting its response and
    comparing it to the response generated from the regular JSON API.
    """
    path = reverse("v1:reports-deployments", args=(deployments_report.report.id,))
    gzip_response = client_logged_in.get(
        path, headers={"Accept": "application/json+gzip"}
    )
    assert (
        gzip_response.ok
    ), f"gzip response was not ok; status {gzip_response.status_code}"
    json_response = client_logged_in.get(path, headers={"Accept": "application/json"})
    assert (
        json_response.ok
    ), f"json response was not ok; status {json_response.status_code}"

    extracted_files = extract_files_from_tarball(
        gzip_response.content, decode_json=True
    )
    assert len(extracted_files) == 1
    extracted_file = list(extracted_files.values())[0]
    assert extracted_file == json_response.json()


@pytest.mark.django_db
def test_get_deployment_report_unknown_id_not_found(client_logged_in):
    """Test getting a report for a report ID that does not exist responds with 404."""
    response = client_logged_in.get(reverse("v1:reports-deployments", args=("1",)))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_deployments_report_not_complete_424_failed(client_logged_in):
    """Test getting a report with incomplete status responds with 424."""
    deployments_report = DeploymentReportFactory(
        number_of_fingerprints=0, status=DeploymentsReport.STATUS_PENDING
    )
    response = client_logged_in.get(
        reverse("v1:reports-deployments", args=(deployments_report.report.id,))
    )
    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY


@pytest.mark.django_db
def test_get_deployments_report_cached_csv_not_set():
    """Test getting cached_csv when cached_csv_file_path is not set."""
    deployments_report = DeploymentReportFactory(cached_csv_file_path=None)
    assert deployments_report.cached_csv is None


@pytest.mark.django_db
def test_get_deployments_report_cached_fingerprints_not_set():
    """Test getting cached_fingerprints when its path is not set."""
    # `_set_cached_fingerprints__skip=True` is REQUIRED here because
    # DeploymentReportFactory._set_cached_fingerprints's default behavior causes it to
    # try to set cached_fingerprints before we are ready to set it for this test.
    deployments_report = DeploymentReportFactory(_set_cached_fingerprints__skip=True)
    assert deployments_report.cached_fingerprints is None


@pytest.mark.django_db
def test_get_deployments_report_cached_csv_unsupported_path(faker, caplog):
    """Test getting cached_csv when its path has unexpected parent."""
    unexpected_path = f"/{faker.slug()}/{faker.slug()}.csv"
    deployments_report = DeploymentReportFactory(cached_csv_file_path=unexpected_path)
    expected_error = (
        f"Unsupported parent path for DeploymentsReport {deployments_report.id}"
    )
    caplog.set_level(logging.ERROR)
    with pytest.raises(PermissionError):
        unexpected_data = deployments_report.cached_csv  # noqa: F841
    assert expected_error in caplog.messages[-1]


@pytest.mark.django_db
def test_get_deployments_report_cached_fingerprints_unsupported_path(faker, caplog):
    """Test getting cached_fingerprints when its path has unexpected parent."""
    unexpected_path = f"/{faker.slug()}/{faker.slug()}.json"
    # `_set_cached_fingerprints__skip=True` is REQUIRED here because
    # DeploymentReportFactory._set_cached_fingerprints's default behavior causes it to
    # try to set cached_fingerprints before we are ready to set it for this test.
    deployments_report = DeploymentReportFactory(
        cached_fingerprints_file_path=unexpected_path,
        _set_cached_fingerprints__skip=True,
    )
    expected_error = (
        f"Unsupported parent path for DeploymentsReport {deployments_report.id}"
    )
    caplog.set_level(logging.ERROR)
    with pytest.raises(PermissionError):
        unexpected_data = deployments_report.cached_fingerprints  # noqa: F841
    assert expected_error in caplog.messages[-1]


@pytest.mark.django_db
def test_get_deployments_report_cached_csv_not_found(faker, caplog):
    """Test getting cached_csv when its path does not find a file."""
    not_found_path = f"{cached_files_path()}/{faker.slug()}.csv"
    deployments_report = DeploymentReportFactory(cached_csv_file_path=not_found_path)
    expected_error = (
        f"Cached CSV file for DeploymentsReport {deployments_report.id} "
        f"not found at '{not_found_path}'"
    )
    caplog.set_level(logging.ERROR)
    with pytest.raises(FileNotFoundError):
        unexpected_data = deployments_report.cached_csv  # noqa: F841
    assert expected_error in caplog.messages[-1]


@pytest.mark.django_db
def test_get_deployments_report_cached_fingerprints_not_found(faker, caplog):
    """Test getting cached_fingerprints when its path does not find a file."""
    not_found_path = f"{cached_files_path()}/{faker.slug()}.json"
    # `_set_cached_fingerprints__skip=True` is REQUIRED here because
    # DeploymentReportFactory._set_cached_fingerprints's default behavior causes it to
    # try to set cached_fingerprints before we are ready to set it for this test.
    deployments_report = DeploymentReportFactory(
        cached_fingerprints_file_path=not_found_path,
        _set_cached_fingerprints__skip=True,
    )
    expected_error = (
        f"Cached fingerprints file for DeploymentsReport {deployments_report.id} "
        f"not found at '{not_found_path}'"
    )
    caplog.set_level(logging.ERROR)
    with pytest.raises(FileNotFoundError):
        unexpected_data = deployments_report.cached_fingerprints  # noqa: F841
    assert expected_error in caplog.messages[-1]


@pytest.mark.django_db
def test_set_deployments_report_set_cached_csv_file_already_exists(
    mocker, caplog, faker
):
    """Test setting cached_csv when file already exists at the path."""
    expected_warning = "Overwriting existing file at"
    caplog.set_level(logging.WARNING)
    original_csv_content = (
        f"{faker.slug()},{faker.slug()}\r\n\r\n{faker.slug()},{faker.slug()}\r\n"
    )
    updated_csv_content = (
        f"{faker.slug()},{faker.slug()}\r\n\r\n{faker.slug()},{faker.slug()}\r\n"
    )

    mock_time = mocker.patch.object(time_module, "time")
    mock_time.return_value = faker.pyint()
    deployments_report = DeploymentReportFactory(cached_csv_file_path=None)
    deployments_report.cached_csv = original_csv_content
    assert deployments_report.cached_csv == original_csv_content
    assert not caplog.messages

    deployments_report.cached_csv = updated_csv_content
    assert deployments_report.cached_csv == updated_csv_content
    assert expected_warning in caplog.messages[-1]


@pytest.mark.django_db
def test_set_deployments_report_set_cached_fingerprints_file_already_exists(
    mocker, caplog, faker
):
    """Test setting cached_fingerprints when file already exists at the path."""
    expected_warning = "Overwriting existing file at"
    caplog.set_level(logging.WARNING)
    original_dict_content = {faker.slug(): faker.slug()}
    updated_dict_content = {faker.slug(): faker.slug()}

    mock_time = mocker.patch.object(time_module, "time")
    mock_time.return_value = faker.pyint()
    # `_set_cached_fingerprints__skip=True` is REQUIRED here because
    # DeploymentReportFactory._set_cached_fingerprints's default behavior causes it to
    # try to set cached_fingerprints before we are ready to set it for this test.
    deployments_report = DeploymentReportFactory(_set_cached_fingerprints__skip=True)
    deployments_report.cached_fingerprints = original_dict_content
    assert deployments_report.cached_fingerprints == original_dict_content
    assert expected_warning not in caplog.messages

    deployments_report.cached_fingerprints = updated_dict_content
    assert deployments_report.cached_fingerprints == updated_dict_content
    assert expected_warning in caplog.messages[-1]
