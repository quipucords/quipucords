"""Test the insights report endpoint (/api/v1/reports/{id}/insights/)."""

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from api.common.common_report import create_filename
from api.models import DeploymentsReport
from tests.factories import DeploymentReportFactory
from tests.report_utils import extract_files_from_tarball


def validate_data(
    data: dict, deployment_report: DeploymentsReport, expected_number_of_slices: int = 2
):
    """Validate insights report data."""
    report_id = deployment_report.report.id
    metadata_filename = f"report_id_{report_id}/metadata.json"
    assert create_filename("metadata", "json", report_id) == metadata_filename
    assert metadata_filename in data.keys()

    report_slices = {}
    for key, value in data.items():
        assert f"report_id_{report_id}/" in key
        if key != metadata_filename:
            report_slices[key] = value
    report_slices_in_metadata = data[metadata_filename]["report_slices"]
    assert len(report_slices_in_metadata) == expected_number_of_slices, (
        "unexpected number of report slices"
    )

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
    assert total_returned_hosts_num == len(expected_bios_uuids), (
        "unexpected hosts count"
    )

    # Assert that the Insights report has all the expected installed_products.
    expected_installed_products = [
        installed_product
        for host in deployment_report.system_fingerprints.all()
        for installed_product in host.installed_products
    ]
    # SystemFingerprintFactory should have created at least one installed_product.
    assert len(expected_installed_products) > 0
    # Ugly but yes this is how you navigate to this data in our Insights report:
    returned_installed_products = [
        installed_product
        for slice_key in report_slices
        for host in report_slices[slice_key]["hosts"]
        for installed_product in host["system_profile"]["installed_products"]
    ]
    # installed_products objects should look like:
    # {"id": "12345", "name": "My Amazing Product"}
    # Based on the specification here:
    # https://github.com/RedHatInsights/insights-host-inventory/blob/986a8323f6d5d94ad721a9746cd50f383dd2594c/swagger/system_profile.spec.yaml#L87  # noqa: E501
    for installed_product in returned_installed_products:
        assert "id" in installed_product
        assert "name" in installed_product
    # We can't use sets to compare installed_products because dicts aren't hashable; so,
    # we sort them before comparing in case the list elements were ordered differently.
    expected_installed_products = sorted(
        expected_installed_products, key=lambda p: (p["id"], p["name"])
    )
    returned_installed_products = sorted(
        returned_installed_products, key=lambda p: (p["id"], p["name"])
    )
    assert returned_installed_products == expected_installed_products


@pytest.mark.django_db
def test_get_insights_report_as_json(client_logged_in):
    """Retrieve insights report as JSON and verify it contains all data (no slicing)."""
    deployment_report = DeploymentReportFactory(
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployment_report.report.id
    response = client_logged_in.get(reverse("v1:reports-insights", args=(report_id,)))
    assert response.ok, f"response was not ok; status {response.status_code}"

    # mock slice size so we can expect result to contain all data without slicing
    with override_settings(QUIPUCORDS_INSIGHTS_REPORT_SLICE_SIZE=99999):
        response_json = response.json()
    validate_data(response_json, deployment_report, expected_number_of_slices=1)


@pytest.mark.django_db
def test_get_insights_report_as_json_sliced(client_logged_in):
    """Retrieve insights report as JSON with sliced data."""
    deployment_report = DeploymentReportFactory(
        number_of_fingerprints=3,
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployment_report.report.id
    # mock slice size so we can expect 2 slices on this test
    with override_settings(QUIPUCORDS_INSIGHTS_REPORT_SLICE_SIZE=2):
        response = client_logged_in.get(
            reverse("v1:reports-insights", args=(report_id,))
        )
    assert response.ok, f"response was not ok; status {response.status_code}"
    response_json = response.json()
    validate_data(response_json, deployment_report)


@pytest.mark.django_db
def test_get_insights_report_as_tarball_sliced(client_logged_in):
    """Retrieve insights report as a tarball (.tar.gz) with sliced data."""
    deployments_report = DeploymentReportFactory(
        number_of_fingerprints=11,
        status=DeploymentsReport.STATUS_COMPLETE,
    )
    report_id = deployments_report.report.id
    # mock slice size so we can expect 2 slices on this test
    with override_settings(QUIPUCORDS_INSIGHTS_REPORT_SLICE_SIZE=10):
        response = client_logged_in.get(
            reverse("v1:reports-insights", args=(report_id,)),
            {"format": "tar.gz"},
        )
    assert response.ok, f"response was not ok; status {response.status_code}"
    # reformat tarball to match json report
    data = extract_files_from_tarball(
        response.content, strip_dirs=False, decode_json=True
    )
    validate_data(data, deployments_report)


@pytest.mark.django_db
def test_get_insights_report_unknown_id_not_found(client_logged_in):
    """Fail to get an Insights for report id that doesn't exist."""
    response = client_logged_in.get(reverse("v1:reports-insights", args=("999",)))
    assert response.status_code == status.HTTP_404_NOT_FOUND
