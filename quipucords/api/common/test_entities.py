# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test common entities."""

from itertools import chain

import pytest

from api.common.entities import ReportEntity, ReportSlice
from api.models import SystemFingerprint
from tests.factories import DeploymentReportFactory, SystemFingerprintFactory


@pytest.fixture
def deployment_reports():
    """Return a list of deployment reports with variable number of fingerprints."""
    return DeploymentReportFactory.create_batch(size=5)


@pytest.fixture
def report_entity():
    """Return a report entity with 100 hosts."""
    deployment_report = DeploymentReportFactory.build(id=42)
    fingerprints = SystemFingerprintFactory.build_batch(100)
    return ReportEntity(deployment_report, fingerprints)


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


class TestReportSlicing:
    """Test ReportSliceEntity and ReportEntity slicing mechanism."""

    def test_hosts(self, report_entity):
        """Check if hosts from slice report match the hosts subset from parent report."""  # noqa: E501
        report_slice = ReportSlice(
            parent_report=report_entity, slice_start=1, slice_end=2
        )
        assert len(report_slice.hosts) == 1
        assert report_slice.hosts == report_entity.hosts[1:2]

    @pytest.mark.parametrize(
        "slice_size_limit,slice_sizes",
        [
            (10, 10 * [10]),
            (50, 2 * [50]),
            (99, [99, 1]),
        ],
    )
    def test_slicing(
        self,
        slice_size_limit,
        slice_sizes,
        report_entity: ReportEntity,
    ):
        """
        Test slicing mechanism.

        Check if slices sizes and content match whats expected.
        """
        # override slice_size_limit
        report_entity.slice_size_limit = slice_size_limit
        assert [len(s.hosts) for s in report_entity.slices.values()] == slice_sizes
        hosts_from_slices = list(
            chain.from_iterable(s.hosts for s in report_entity.slices.values())
        )
        assert hosts_from_slices == report_entity.hosts
