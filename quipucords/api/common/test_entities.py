# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test common entities."""

import pytest

from api.common.entities import ReportEntity
from api.models import SystemFingerprint
from tests.factories import DeploymentReportFactory


@pytest.fixture
def deployment_reports():
    """Return a list of deployment reports with variable number of fingerprints."""
    return DeploymentReportFactory.create_batch(size=5)


@pytest.mark.django_db
class TestReportEntity:
    """Test ReportEntity."""

    def test_from_report_id(self, django_assert_max_num_queries, deployment_reports):
        """Test ReportEntity factory method "from_report_id"."""
        # pick the id for one of the reports
        report_id = deployment_reports[0].id

        with django_assert_max_num_queries(1):
            report = ReportEntity.from_report_id(report_id)

        assert isinstance(report, ReportEntity)

        assert report.report_id == report_id
        fingerprint_ids = set(host.id for host in report.hosts)

        fingerprints_from_report = SystemFingerprint.objects.filter(
            deployment_report_id=report_id
        )
        assert set(f.id for f in fingerprints_from_report) == fingerprint_ids

    def test_from_report_id_deployment_not_found(self):
        """Check if the proper error is raised."""
        with pytest.raises(
            SystemFingerprint.DoesNotExist,
            match="Report with 'report_id=42' either doesn't exist or don't have hosts.",  # noqa: E501
        ):
            ReportEntity.from_report_id(42)

    def test_from_report_id_fingerprint_not_fount(self):
        """Check if the proper error is raised."""
        deployment_report = DeploymentReportFactory(number_of_fingerprints=0)
        with pytest.raises(SystemFingerprint.DoesNotExist):
            ReportEntity.from_report_id(deployment_report.id)
