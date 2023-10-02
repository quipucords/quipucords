"""Test the insights report endpoint (/api/v1/reports/{id}/insights/)."""
from django.test import override_settings
from rest_framework import status

from api.common.common_report import create_filename
from api.models import DeploymentsReport
from tests.factories import DeploymentReportFactory, SystemFingerprintFactory
from tests.report_utils import extract_tarball_from_response

INSIGHTS_API_PATH = "/api/v1/reports/{0}/insights/"


def validate_data(
    data: dict, deployment_report: DeploymentsReport, expected_number_of_slices: int = 2
):
    """Validate insights report data."""
    report_id = deployment_report.report.id
    metadata_filename = f"report_id_{report_id}/metadata.json"
    assert create_filename("metadata", "json", report_id) == metadata_filename
    assert metadata_filename in data.keys()

    report_slices = {}
    for key in data:
        assert f"report_id_{report_id}/" in key
        if key != metadata_filename:
            report_slices[key] = data[key]
    report_slices_in_metadata = data[metadata_filename]["report_slices"]
    assert (
        len(report_slices_in_metadata) == expected_number_of_slices
    ), "unexpected number of report slices"

    total_returned_hosts_num = 0
    for key_1, key_2 in zip(report_slices_in_metadata, report_slices):
        # metadata number_hosts should match the actual number of hosts in a slice
        assert report_slices_in_metadata[key_1]["number_hosts"] == len(
            report_slices[key_2]["hosts"]
        )
        # used later to check for the total size
        total_returned_hosts_num += len(report_slices[key_2]["hosts"])

    # no hosts lost
    returned_bios_uuids = {
        host["bios_uuid"]
        for slice_key in report_slices
        for host in report_slices[slice_key]["hosts"]
    }
    expected_bios_uuids = {
        host.bios_uuid for host in deployment_report.system_fingerprints.all()
    }
    assert returned_bios_uuids == expected_bios_uuids, "unexpected bios uuids"
    # sum of all hosts in a slice is equal to
    # the total number of host (before call)
    assert total_returned_hosts_num == len(
        expected_bios_uuids
    ), "unexpected hosts count"


def test_get_insights_report_as_json(django_client):
    """Retrieve insights report as JSON and verify it contains all data (no slicing)."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployment_report.report.id
    response = django_client.get(INSIGHTS_API_PATH.format(report_id))
    assert response.ok, f"response was not ok; status {response.status_code}"

    # mock slice size so we can expect result to contain all data without slicing
    with override_settings(QPC_INSIGHTS_REPORT_SLICE_SIZE=99999):
        response_json = response.json()
    validate_data(response_json, deployment_report, expected_number_of_slices=1)


def test_get_insights_report_as_json_sliced(django_client):
    """Retrieve insights report as JSON with sliced data."""
    deployment_report = DeploymentReportFactory(
        number_of_fingerprints=3,
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployment_report.report.id
    # mock slice size so we can expect 2 slices on this test
    with override_settings(QPC_INSIGHTS_REPORT_SLICE_SIZE=2):
        response = django_client.get(INSIGHTS_API_PATH.format(report_id))
    assert response.ok, f"response was not ok; status {response.status_code}"
    response_json = response.json()
    validate_data(response_json, deployment_report)


def test_get_insights_report_as_tarball_sliced(django_client):
    """Retrieve insights report as a tarball (.tar.gz) with sliced data."""
    deployments_report = DeploymentReportFactory(
        number_of_fingerprints=11,
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployments_report.report.id
    # mock slice size so we can expect 2 slices on this test
    with override_settings(QPC_INSIGHTS_REPORT_SLICE_SIZE=10):
        response = django_client.get(
            INSIGHTS_API_PATH.format(report_id), params={"format": "tar.gz"}
        )
    assert response.ok, f"response was not ok; status {response.status_code}"
    # reformat tarball to match json report
    data = extract_tarball_from_response(response, strip_dirs=False, decode_json=True)
    validate_data(data, deployments_report)


def test_get_insights_report_not_found_because_no_fingerprints(django_client):
    """Retrieve Insights report, but it does not exist due to lack of fingerprints."""
    deployment_report = DeploymentReportFactory.create(
        number_of_fingerprints=0,
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployment_report.report.id
    # fingerprint without canonical facts
    SystemFingerprintFactory.create(
        deployment_report_id=deployment_report.id,
        name=None,
        bios_uuid=None,
        insights_client_id=None,
        ip_addresses=None,
        mac_addresses=None,
        subscription_manager_id=None,
        cloud_provider=None,
    )
    fingerprint_count = deployment_report.system_fingerprints.count()
    assert (
        fingerprint_count == 1
    ), f"unexpected fingerprint count {fingerprint_count} != 1"
    response = django_client.get(INSIGHTS_API_PATH.format(report_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_insights_report_invalid_id_not_found(django_client):
    """Fail to get an Insights report for an invalid id."""
    response = django_client.get(INSIGHTS_API_PATH.format("invalid"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_insights_report_unknown_id_not_found(django_client):
    """Fail to get an Insights for report id that doesn't exist."""
    response = django_client.get(INSIGHTS_API_PATH.format("999"))
    assert response.status_code == status.HTTP_404_NOT_FOUND
