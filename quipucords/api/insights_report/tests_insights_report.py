#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the insights report endpoint."""

import json
import tarfile
from io import BytesIO

import pytest
from django.test import override_settings
from rest_framework import status

from api.common.common_report import create_filename
from api.models import DeploymentsReport
from tests.factories import DeploymentReportFactory, SystemFingerprintFactory


@pytest.mark.dbcompat
@pytest.mark.django_db
class TestInsightsReport:
    """Tests against the Insights reports function."""

    def test_get_insights_report_200_exists(self, client):
        """Retrieve insights report."""
        deployment_report = DeploymentReportFactory(
            number_of_fingerprints=3,
            status=DeploymentsReport.STATUS_COMPLETE,
        )
        url = f"/api/v1/reports/{deployment_report.id}/insights/"
        # mock slice size so we can expect 2 slices on this test
        with override_settings(QPC_INSIGHTS_REPORT_SLICE_SIZE=2):
            response = client.get(url)
        assert response.status_code == 200, response.json()
        response_json = response.json()
        self.validate_data(response_json, deployment_report)

    def test_get_insights_report_tarball_200_exists(self, client):
        """Retrieve insights report."""
        deployments_report = DeploymentReportFactory(
            number_of_fingerprints=11,
            status=DeploymentsReport.STATUS_COMPLETE,
        )
        url = f"/api/v1/reports/{deployments_report.id}/insights/?format=tar.gz"
        # mock slice size so we can expect 2 slices on this test
        with override_settings(QPC_INSIGHTS_REPORT_SLICE_SIZE=10):
            response = client.get(url)
        assert response.status_code == 200
        # reformat tarball to match json report
        with tarfile.open(fileobj=BytesIO(response.content)) as tar:
            restored_files = (
                json.loads(tar.extractfile(file).read()) for file in tar.getmembers()
            )
            # tar.getnames / getmembers follow the same order, allowing this one-liner
            data = dict(zip(tar.getnames(), restored_files))
        self.validate_data(data, deployments_report)

    def validate_data(self, data: dict, deployment_report: DeploymentsReport):
        """Validate insights report data."""
        assert create_filename("metadata", "json", deployment_report.id) in data.keys()
        report_slices = {}
        metadata_filename = f"report_id_{deployment_report.id}/metadata.json"
        for key in data:
            assert f"report_id_{deployment_report.id}/" in key
            if key != metadata_filename:
                report_slices[key] = data[key]
        # metadata slice number_hosts matches the actual
        # number of hosts in a slice
        report_slices_in_metadata = data[metadata_filename]["report_slices"]
        assert len(report_slices_in_metadata) == 2
        total_returned_hosts_num = 0
        for key_1, key_2 in zip(report_slices_in_metadata, report_slices):
            assert report_slices_in_metadata[key_1]["number_hosts"] == len(
                report_slices[key_2]["hosts"]
            )
            # used later to check for the total size
            total_returned_hosts_num += len(report_slices[key_2]["hosts"])
        # no hosts lost
        returned_host_names = {
            host["bios_uuid"]
            for slice_key in report_slices  # pylint: disable=consider-using-dict-items
            for host in report_slices[slice_key]["hosts"]
        }
        expected_host_names = {
            host.bios_uuid for host in deployment_report.system_fingerprints.all()
        }
        assert returned_host_names == expected_host_names
        # sum of all hosts in a slice is equal to
        # the total number of host (before call)
        assert total_returned_hosts_num == len(expected_host_names)

    def test_get_insights_report_200_generate_exists(self, client):
        """Retrieve insights report."""
        deployment_report = DeploymentReportFactory(
            status=DeploymentsReport.STATUS_COMPLETE,
        )
        url = f"/api/v1/reports/{deployment_report.id}/insights/"
        response = client.get(url)
        assert response.status_code == 200
        response_json = response.json()

        assert (
            create_filename("metadata", "json", deployment_report.id)
            in response_json.keys()
        )
        for key in response_json:
            assert f"report_id_{deployment_report.id}/" in key

    def test_get_insights_report_404_no_canonical(self, client):
        """Retrieve insights report."""
        deployment_report = DeploymentReportFactory.create(
            number_of_fingerprints=0,
            status=DeploymentsReport.STATUS_COMPLETE,
        )
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
        assert deployment_report.system_fingerprints.count() == 1
        url = f"/api/v1/reports/{deployment_report.id}/insights/"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_insights_report_bad_id(self, client):
        """Fail to get a report for bad id."""
        url = "/api/v1/reports/string/insights/"

        # Query API
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_insights_nonexistent(self, client):
        """Fail to get a report for report id that doesn't exist."""
        url = "/api/v1/reports/999/insights/"

        # Query API
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
