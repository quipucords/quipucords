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
from rest_framework.reverse import reverse

from api.common.common_report import REPORT_TYPE_DEPLOYMENT, REPORT_TYPE_DETAILS
from api.deployments_report.model import DeploymentsReport
from api.deployments_report.util import create_deployments_csv
from api.deployments_report.view import build_cached_json_report
from api.details_report.serializer import DetailsReportSerializer
from api.details_report.util import create_details_csv
from api.reports.model import Report
from constants import SCAN_JOB_LOG
from tests.constants import (
    FILENAME_DEPLOYMENTS_CSV,
    FILENAME_DEPLOYMENTS_JSON,
    FILENAME_DETAILS_CSV,
    FILENAME_DETAILS_JSON,
    FILENAME_SHA256SUM,
)
from tests.factories import DeploymentReportFactory, ReportFactory
from tests.report_utils import extract_files_from_tarball

TARBALL_ALWAYS_EXPECTED_FILENAMES = {
    FILENAME_SHA256SUM,
    FILENAME_DEPLOYMENTS_CSV,
    FILENAME_DEPLOYMENTS_JSON,
    FILENAME_DETAILS_CSV,
    FILENAME_DETAILS_JSON,
}


def get_serialized_report_data(report: Report) -> dict:
    """Get the serialized form of the Report, simulating a view's processing."""
    # We need to refresh from DB because something about how the factory created the
    # Report object here can cause flaky, unexpected failures in the serializer.
    # Maybe there's a bug in the factories or how we're using them?
    report.refresh_from_db()
    report_data = DetailsReportSerializer(report).data
    report_data.pop("cached_csv", None)  # because the view does this before returning
    return report_data


@pytest.mark.django_db
def test_report_without_logs(client_logged_in, caplog):
    """Explicitly test report without logs."""
    caplog.set_level(logging.WARNING)
    deployment = DeploymentReportFactory.create()
    report_id = deployment.report.id
    response = client_logged_in.get(reverse("v1:reports-detail", args=(report_id,)))
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
    deployments_report: DeploymentsReport = DeploymentReportFactory(report=None)
    ReportFactory(generate_raw_facts=True, deployment_report=deployments_report)
    scan_job_id = deployments_report.report.scanjob.id
    log_file = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
        scan_job_id=scan_job_id, output_type="test"
    )
    log_file.write_text(faker.paragraph())
    assert len(deployments_report.report.sources) > 0  # to verify we have some data
    return deployments_report


@pytest.mark.django_db
def test_report_with_logs(client_logged_in, deployment_with_logs):
    """Test if scan job logs are included in tarball when present."""
    report = deployment_with_logs.report
    scan_job_id = report.scanjob.id
    response = client_logged_in.get(reverse("v1:reports-detail", args=(report.id,)))
    assert response.ok, response.text
    expected_files = {
        f"report_id_{report.id}/{fname}"
        for fname in TARBALL_ALWAYS_EXPECTED_FILENAMES.union(
            {f"scan-job-{scan_job_id}-test.txt"}
        )
    }
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        assert set(tarball.getnames()) == expected_files


@pytest.mark.django_db
def test_report_tarball_sha256sum(client_logged_in, deployment_with_logs):
    """Verify SHA256SUM files and digests are correct."""
    deployments_report = deployment_with_logs
    response = client_logged_in.get(
        reverse("v1:reports-detail", args=(deployments_report.report.id,))
    )
    assert response.ok, response.text
    files_contents = extract_files_from_tarball(response.content)
    expected_filenames = TARBALL_ALWAYS_EXPECTED_FILENAMES.union(
        {f"scan-job-{deployments_report.report.scanjob.id}-test.txt"}
    )
    assert expected_filenames == set(
        files_contents.keys()
    ), "incorrect files in tarball"

    sha256sum_dict = dict(
        (line.split()[1], line.split()[0])  # swap order to look like {name: contents}
        for line in files_contents[FILENAME_SHA256SUM].decode().splitlines()
    )
    assert expected_filenames.difference({FILENAME_SHA256SUM}) == set(
        sha256sum_dict.keys()
    ), "incorrect files listed in SHA256SUM file"

    for name, downloaded_digest in sha256sum_dict.items():
        assert name in files_contents
        recalculated_digest = hashlib.sha256(files_contents[name]).hexdigest()
        assert (
            downloaded_digest == recalculated_digest
        ), f"incorrect SHA256SUM digest for {name}"


@pytest.mark.django_db
def test_report_tarball_details_json(
    client_logged_in, deployment_with_logs: DeploymentsReport
):
    """Test report tarball contains expected details.json."""
    deployments_report = deployment_with_logs
    report = deployments_report.report
    tarball_response = client_logged_in.get(
        reverse("v1:reports-detail", args=(deployments_report.report.id,))
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_files_from_tarball(tarball_response.content)
    assert FILENAME_DETAILS_JSON in files_contents
    tarball_details_json = json.loads(files_contents[FILENAME_DETAILS_JSON].decode())

    # Compare tarball details.json contents with the standalone API's response.
    api_details_response = client_logged_in.get(
        reverse("v1:reports-details", args=(deployments_report.report.id,)),
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


@pytest.mark.django_db
def test_report_tarball_deployments_json(
    client_logged_in, deployment_with_logs: DeploymentsReport
):
    """Test report tarball contains expected deployments.json."""
    deployments_report = deployment_with_logs
    tarball_response = client_logged_in.get(
        reverse("v1:reports-detail", args=(deployments_report.report.id,))
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_files_from_tarball(tarball_response.content)
    assert FILENAME_DEPLOYMENTS_JSON in files_contents
    tarball_deployments_json = json.loads(
        files_contents[FILENAME_DEPLOYMENTS_JSON].decode()
    )

    # Compare tarball details.json contents with our model serialized.
    model_data_as_json = build_cached_json_report(deployments_report)
    assert model_data_as_json == tarball_deployments_json

    # Compare tarball deployments.json contents with the standalone API's response.
    api_deployments_response = client_logged_in.get(
        reverse("v1:reports-deployments", args=(deployments_report.report.id,)),
        headers={"Accept": "application/json"},
    )
    assert api_deployments_response.ok, api_deployments_response.text
    api_deployments_json = api_deployments_response.json()
    assert tarball_deployments_json == api_deployments_json

    # Sanity-check the basic structure of the tarball deployments.json directly.
    assert tarball_deployments_json["report_id"] == deployments_report.report.id
    assert tarball_deployments_json["report_type"] == REPORT_TYPE_DEPLOYMENT


@pytest.mark.django_db
def test_report_details_csv(client_logged_in, deployment_with_logs: DeploymentsReport):
    """Test report tarball contains expected details.csv."""
    deployments_report = deployment_with_logs
    tarball_response = client_logged_in.get(
        reverse("v1:reports-detail", args=(deployments_report.report.id,))
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_files_from_tarball(tarball_response.content)
    assert FILENAME_DETAILS_CSV in files_contents
    tarball_details_csv = files_contents[FILENAME_DETAILS_CSV].decode()

    # Compare tarball details.csv contents with the standalone API's response.
    details_csv_response = client_logged_in.get(
        reverse("v1:reports-details", args=(deployments_report.report.id,)),
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


@pytest.mark.django_db
def test_report_deployments_csv(
    client_logged_in, deployment_with_logs: DeploymentsReport
):
    """Test report tarball contains expected deployments.csv."""
    deployments_report = deployment_with_logs
    tarball_response = client_logged_in.get(
        reverse("v1:reports-detail", args=(deployments_report.report.id,))
    )
    assert tarball_response.ok, tarball_response.text

    files_contents = extract_files_from_tarball(tarball_response.content)
    assert FILENAME_DEPLOYMENTS_CSV in files_contents

    # Compare tarball deployments.csv contents with the standalone API's response.
    tarball_deployments_csv = files_contents[FILENAME_DEPLOYMENTS_CSV].decode()
    deployments_csv_response = client_logged_in.get(
        reverse("v1:reports-deployments", args=(deployments_report.report.id,)),
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
