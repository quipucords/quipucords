"""
Test the reports API.

This module confirms that the report download tarball (.tar.gz) has all expected files.
That may include (but not necessarily be limited to): "SHA256SUM", "deployments.csv",
"deployments.json", "details.csv", "details.json", and "scan-job-{some_id}.txt".

For the individual report files, these tests generally check the following conditions:

* Verify the file in the tarball matches the individual report API's response.
* Verify the file in the tarball matches what our model serializer generates.
* Directly sanity check a few structural elements or fields directly against the model.

These tests effectively exercise ReportsGzipRenderer by requesting the report view
despite not instantiating it directly. (I'm including this comment to help future devs
searching for "ReportsGzipRenderer" in our repo.)
"""

import csv
import hashlib
import json
import logging
import tarfile
from io import BytesIO

import pytest
from rest_framework.renderers import JSONRenderer

from api.common.common_report import REPORT_TYPE_DEPLOYMENT, REPORT_TYPE_DETAILS
from api.deployments_report.model import DeploymentsReport
from api.deployments_report.util import create_deployments_csv
from api.deployments_report.view import build_cached_json_report
from api.details_report.serializer import DetailsReportSerializer
from api.details_report.util import create_details_csv
from api.reports.model import Report
from constants import SCAN_JOB_LOG
from tests.factories import DeploymentReportFactory
from tests.report_utils import extract_tarball_from_response

DEPLOYMENTS_CSV_FILENAME = "deployments.csv"
DEPLOYMENTS_JSON_FILENAME = "deployments.json"
DETAILS_CSV_FILENAME = "details.csv"
DETAILS_JSON_FILENAME = "details.json"
SHA256SUM_FILENAME = "SHA256SUM"
TARBALL_ALWAYS_EXPECTED_FILENAMES = {
    SHA256SUM_FILENAME,
    DEPLOYMENTS_CSV_FILENAME,
    DEPLOYMENTS_JSON_FILENAME,
    DETAILS_CSV_FILENAME,
    DETAILS_JSON_FILENAME,
}

REPORTS_API_PATH = "/api/v1/reports/{0}/"
DEPLOYMENTS_API_PATH = "/api/v1/reports/{0}/deployments/"
DETAILS_API_PATH = "/api/v1/reports/{0}/details/"


def get_serialized_report_data(report: Report) -> dict:
    """Get the serialized form of the Report, simulating a view's processing."""
    # We need to refresh from DB because something about how the factory created the
    # Report object here can cause unexpected failures in the serializer. Maybe a bug?
    report.refresh_from_db()
    report_data = DetailsReportSerializer(report).data
    report_data.pop("cached_csv", None)  # because the view does this before returning
    return report_data


def test_report_without_logs(django_client, caplog):
    """Explicitly test report without logs."""
    caplog.set_level(logging.WARNING)
    deployment = DeploymentReportFactory.create()
    report_id = deployment.report.id
    response = django_client.get(REPORTS_API_PATH.format(report_id))
    assert response.ok, response.text
    assert f"No logs were found for report_id={report_id}" in caplog.messages
    expected_files = {
        f"report_id_{report_id}/{fname}" for fname in TARBALL_ALWAYS_EXPECTED_FILENAMES
    }
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        assert set(tarball.getnames()) == expected_files


@pytest.fixture
def deployment_with_logs(settings, faker):
    """Return a completed DeploymentReport instance that has associate scan job logs."""
    deployments_report: DeploymentsReport = DeploymentReportFactory.create()
    scan_job_id = deployments_report.report.scanjob.id
    log_file = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
        scan_job_id=scan_job_id, output_type="test"
    )
    log_file.write_text(faker.paragraph())
    assert len(deployments_report.report.sources) > 0  # to verify we have some data
    return deployments_report


def test_report_with_logs(django_client, deployment_with_logs):
    """Test if scan job logs are included in tarball when present."""
    report = deployment_with_logs.report
    scan_job_id = report.scanjob.id
    response = django_client.get(REPORTS_API_PATH.format(report.id))
    assert response.ok, response.text
    expected_files = {
        f"report_id_{report.id}/{fname}"
        for fname in TARBALL_ALWAYS_EXPECTED_FILENAMES.union(
            {f"scan-job-{scan_job_id}-test.txt"}
        )
    }
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        assert set(tarball.getnames()) == expected_files


def test_report_tarball_sha256sum(django_client, deployment_with_logs):
    """Verify SHA256SUM files and digests are correct."""
    deployments_report = deployment_with_logs
    response = django_client.get(REPORTS_API_PATH.format(deployments_report.report.id))
    assert response.ok, response.text

    files_contents = extract_tarball_from_response(response)
    expected_filenames = TARBALL_ALWAYS_EXPECTED_FILENAMES.union(
        {f"scan-job-{deployments_report.report.scanjob.id}-test.txt"}
    )
    assert expected_filenames == set(
        files_contents.keys()
    ), "incorrect files in tarball"

    sha256sum_dict = dict(
        (line.split()[1], line.split()[0])  # swap order to look like {name: contents}
        for line in files_contents[SHA256SUM_FILENAME].decode().splitlines()
    )
    assert expected_filenames.difference({SHA256SUM_FILENAME}) == set(
        sha256sum_dict.keys()
    ), "incorrect files listed in SHA256SUM file"

    for name, downloaded_digest in sha256sum_dict.items():
        assert name in files_contents
        recalculated_digest = hashlib.sha256(files_contents[name]).hexdigest()
        assert (
            downloaded_digest == recalculated_digest
        ), f"incorrect SHA256SUM digest for {name}"


def test_report_tarball_details_json(
    django_client, deployment_with_logs: DeploymentsReport
):
    """Test report tarball contains expected details.json."""
    deployments_report = deployment_with_logs
    report = deployments_report.report
    tarball_response = django_client.get(
        REPORTS_API_PATH.format(deployments_report.report.id)
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_tarball_from_response(tarball_response)
    assert DETAILS_JSON_FILENAME in files_contents
    tarball_details_json = json.loads(files_contents[DETAILS_JSON_FILENAME].decode())

    # Compare tarball details.json contents with the standalone API's response.
    api_details_response = django_client.get(
        DETAILS_API_PATH.format(deployments_report.report.id),
        headers={"Accept": "application/json"},
    )
    assert api_details_response.ok, api_details_response.text
    api_details_json = api_details_response.json()
    assert tarball_details_json == api_details_json

    # Compare tarball details.json contents with our model serialized.
    serialized_report_data = get_serialized_report_data(report)
    expected_report_json = json.loads(
        JSONRenderer().render(data=serialized_report_data)
    )
    assert expected_report_json == tarball_details_json

    # Sanity-check some tarball details.json fields directly with our stored model.
    assert tarball_details_json["report_id"] == report.id
    assert tarball_details_json["report_type"] == REPORT_TYPE_DETAILS
    assert tarball_details_json["report_platform_id"] == str(report.report_platform_id)


def test_report_tarball_deployments_json(
    django_client, deployment_with_logs: DeploymentsReport
):
    """Test report tarball contains expected deployments.json."""
    deployments_report = deployment_with_logs
    tarball_response = django_client.get(
        REPORTS_API_PATH.format(deployments_report.report.id)
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_tarball_from_response(tarball_response)
    assert DEPLOYMENTS_JSON_FILENAME in files_contents
    tarball_deployments_json = json.loads(
        files_contents[DEPLOYMENTS_JSON_FILENAME].decode()
    )

    # Compare tarball details.json contents with our model serialized.
    model_data_as_json = build_cached_json_report(deployments_report)
    assert model_data_as_json == tarball_deployments_json

    # Compare tarball deployments.json contents with the standalone API's response.
    api_deployments_response = django_client.get(
        DEPLOYMENTS_API_PATH.format(deployments_report.report.id),
        headers={"Accept": "application/json"},
    )
    assert api_deployments_response.ok, api_deployments_response.text
    api_deployments_json = api_deployments_response.json()
    assert tarball_deployments_json == api_deployments_json

    # Sanity-check the basic structure of the tarball deployments.json directly.
    assert tarball_deployments_json["report_id"] == deployments_report.report.id
    assert tarball_deployments_json["report_type"] == REPORT_TYPE_DEPLOYMENT


def test_report_details_csv(django_client, deployment_with_logs: DeploymentsReport):
    """Test report tarball contains expected details.csv."""
    deployments_report = deployment_with_logs
    tarball_response = django_client.get(
        REPORTS_API_PATH.format(deployments_report.report.id)
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_tarball_from_response(tarball_response)
    assert DETAILS_CSV_FILENAME in files_contents
    tarball_details_csv = files_contents[DETAILS_CSV_FILENAME].decode()

    # Compare tarball details.csv contents with the standalone API's response.
    details_csv_response = django_client.get(
        DETAILS_API_PATH.format(deployments_report.report.id),
        headers={"Accept": "text/csv"},
    )
    assert details_csv_response.ok, details_csv_response.text
    assert details_csv_response.text == tarball_details_csv

    # Compare tarball details.csv contents with our model serialized.
    serialized_report_data = get_serialized_report_data(deployments_report.report)
    report_data_csv = create_details_csv(serialized_report_data)
    assert report_data_csv == tarball_details_csv

    # Sanity-check the basic structure of the tarball details.csv directly.
    tarball_details_csv_lines = list(csv.reader(tarball_details_csv.splitlines()))
    expected_csv_first_line = [
        "Report ID",
        "Report Type",
        "Report Version",
        "Report Platform ID",
        "Number Sources",
    ]
    assert tarball_details_csv_lines[0] == expected_csv_first_line
    # Why 12? We expect three separate table headers in the file, two section markers,
    # four blank lines, and at least one line per table. Yes, this CSV is a mess. >:(
    assert len(tarball_details_csv_lines) >= 12


def test_report_deployments_csv(django_client, deployment_with_logs: DeploymentsReport):
    """Test report tarball contains expected deployments.csv."""
    deployments_report = deployment_with_logs
    tarball_response = django_client.get(
        REPORTS_API_PATH.format(deployments_report.report.id)
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_tarball_from_response(tarball_response)
    assert DEPLOYMENTS_CSV_FILENAME in files_contents

    # Compare tarball deployments.csv contents with the standalone API's response.
    tarball_deployments_csv = files_contents[DEPLOYMENTS_CSV_FILENAME].decode()
    deployments_csv_response = django_client.get(
        DEPLOYMENTS_API_PATH.format(deployments_report.report.id),
        headers={"Accept": "text/csv"},
    )
    assert deployments_csv_response.ok, deployments_csv_response.text
    assert deployments_csv_response.text == tarball_deployments_csv

    # Compare tarball deployments.csv contents with our model serialized.
    model_data_as_json = build_cached_json_report(deployments_report)
    model_data_as_csv = create_deployments_csv(model_data_as_json)
    assert model_data_as_csv == tarball_deployments_csv

    # Sanity-check the basic structure of the tarball deployments.csv directly.
    tarball_deployments_csv_lines = list(
        csv.reader(tarball_deployments_csv.splitlines())
    )
    expected_csv_first_line = [
        "Report ID",
        "Report Type",
        "Report Version",
        "Report Platform ID",
    ]
    assert tarball_deployments_csv_lines[0] == expected_csv_first_line
    # Why 7? We expect two separate table headers in the file, one section marker,
    # three blank lines, and at least one line per table. Yes, this CSV is a mess. >:(
    assert len(tarball_deployments_csv_lines) >= 7
