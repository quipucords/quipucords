# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test common entities."""

from datetime import datetime
from itertools import chain

import pytest

from api.common.entities import HostEntity, ReportEntity, ReportSlice
from api.deployments_report.model import DeploymentsReport
from api.models import Product, SystemFingerprint
from tests.factories import DeploymentReportFactory, SystemFingerprintFactory


@pytest.fixture
def deployment_reports():
    """Return a list of deployment reports with variable number of fingerprints."""
    return DeploymentReportFactory.create_batch(size=5)


@pytest.fixture
def fingerprint_wo_products():
    """Return a system fingerprint instance."""
    report = DeploymentReportFactory.create(number_of_fingerprints=1)
    return report.system_fingerprints.get()


@pytest.fixture
def fingerprint_with_products():
    """Return a system fingerprint instance with 3 products."""
    report = DeploymentReportFactory.create(number_of_fingerprints=1)
    sys_fp = report.system_fingerprints.get()
    products = [
        Product(name="JBoss EAP", presence=Product.PRESENT, fingerprint=sys_fp),
        Product(name="JBoss Fuse", presence=Product.ABSENT, fingerprint=sys_fp),
        Product(name="UNKOWN PRODUCT", presence=Product.PRESENT, fingerprint=sys_fp),
    ]
    Product.objects.bulk_create(products)
    return sys_fp


@pytest.fixture(
    params=[
        pytest.lazy_fixture("fingerprint_wo_products"),
        pytest.lazy_fixture("fingerprint_with_products"),
    ]
)
def fingerprint(request):
    """Return a multiplexed system fingerprint."""
    return request.param


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

        with django_assert_max_num_queries(2):
            report = ReportEntity.from_report_id(report_id)
            # ensure products does not trigger another query
            assert isinstance(report.hosts[0].products, set)

        assert isinstance(report, ReportEntity)

        assert report.report_id == report_id
        fingerprint_ids = set(host.id for host in report.hosts)

        fingerprints_from_report = SystemFingerprint.objects.filter(
            deployment_report_id=report_id
        )
        assert set(f.id for f in fingerprints_from_report) == fingerprint_ids

    def test_from_report_id_deployment_not_found(self):
        """Check if the proper error is raised."""
        with pytest.raises(DeploymentsReport.DoesNotExist):
            ReportEntity.from_report_id(42)

    def test_from_report_id_fingerprint_not_fount(self):
        """Check if the proper error is raised."""
        deployment_report = DeploymentReportFactory(number_of_fingerprints=0)
        with pytest.raises(SystemFingerprint.DoesNotExist):
            ReportEntity.from_report_id(deployment_report.id)

    def test_last_discovered_built_from_factory(self, django_assert_num_queries):
        """Test last_discovered property."""
        report_id = DeploymentReportFactory().id
        # query for deployment report to force only deployment report to be loaded
        deployment_report = DeploymentsReport.objects.get(id=report_id)
        report = ReportEntity.from_report_id(deployment_report.id)
        with django_assert_num_queries(0):
            assert isinstance(report.last_discovered, datetime)

    def test_last_discovered_initialized(self, django_assert_num_queries):
        """Test last_discovered property with ReportEntity initialized manually."""
        report_id = DeploymentReportFactory().id
        # query for deployment report to force only deployment report to be loaded
        deployment_report = DeploymentsReport.objects.get(id=report_id)
        report = ReportEntity(
            deployment_report, hosts=deployment_report.system_fingerprints.all()
        )
        with django_assert_num_queries(2):
            assert isinstance(report.last_discovered, datetime)


@pytest.mark.django_db
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
        assert [s.number_of_hosts for s in report_entity.slices.values()] == slice_sizes
        hosts_from_slices = list(
            chain.from_iterable(s.hosts for s in report_entity.slices.values())
        )
        assert hosts_from_slices == report_entity.hosts


@pytest.mark.django_db
class TestHostEntity:
    """Test HostEntity."""

    @classmethod
    def host_init(cls, system_fingerprint) -> HostEntity:
        """Initialize HostEntity using ReportEntity annotated query."""
        report = ReportEntity.from_report_id(system_fingerprint.deployment_report.id)
        return report.hosts[0]

    def test_products_not_implemented(self, fingerprint):
        """Ensure only properly initialized host have products."""
        host = HostEntity(fingerprint, last_discovered=None)
        with pytest.raises(NotImplementedError):
            host.products  # pylint: disable=pointless-statement  # false positive

    @pytest.mark.parametrize(
        "fingerprint,expected_product_names,expected_rh_products_installed",
        [
            (
                pytest.lazy_fixture("fingerprint_wo_products"),
                set(),
                [],
            ),
            (
                pytest.lazy_fixture("fingerprint_with_products"),
                {"JBoss EAP", "UNKOWN PRODUCT"},
                ["EAP"],
            ),
        ],
    )
    def test_products(
        self,
        fingerprint,
        expected_product_names,
        expected_rh_products_installed,
    ):
        """Test products/rh_products_installed properties."""
        host = self.host_init(fingerprint)
        assert host.products == expected_product_names
        assert host.rh_products_installed == expected_rh_products_installed

    def test_products_is_rhel(self, fingerprint):
        """Check if RHEL is added to rh_products_installed when system is rhel."""
        fingerprint.is_redhat = True
        fingerprint.save()
        host = self.host_init(fingerprint)
        assert "RHEL" in host.rh_products_installed

    @pytest.mark.parametrize(
        "cpu_socket_count,vm_host_socket_count,expected_result",
        (
            ("cpu", "host", "cpu"),
            ("cpu", None, "cpu"),
            (None, "host", "host"),
            (None, None, None),
        ),
    )
    def test_number_of_sockets(
        self,
        mocker,
        cpu_socket_count,
        vm_host_socket_count,
        expected_result,
    ):
        """Test number_of_sockets logic."""
        mocked_fingerprint = mocker.Mock(
            cpu_socket_count=cpu_socket_count, vm_host_socket_count=vm_host_socket_count
        )
        host = HostEntity(mocked_fingerprint, None)
        assert host.number_of_sockets == expected_result

    @pytest.mark.parametrize(
        "cpu_core_per_socket,vm_host_core_count,vm_host_socket_count,expected_result",
        (
            (1, 4, 2, 1),
            (None, 4, 2, 2),
            (None, None, 2, None),
            (None, 4, None, None),
            (None, 4, 0, None),
            (None, None, None, None),
        ),
    )
    def test_cores_per_socket(  # pylint: disable=too-many-arguments
        self,
        mocker,
        cpu_core_per_socket,
        vm_host_core_count,
        vm_host_socket_count,
        expected_result,
    ):
        """Test cores_per_socket logic."""
        mocked_fingerprint = mocker.Mock(
            cpu_core_per_socket=cpu_core_per_socket,
            vm_host_core_count=vm_host_core_count,
            vm_host_socket_count=vm_host_socket_count,
        )
        host = HostEntity(mocked_fingerprint, None)
        assert host.cores_per_socket == expected_result
