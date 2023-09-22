"""Test common entities."""

import logging
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


@pytest.mark.dbcompat
@pytest.mark.django_db
class TestReportEntity:
    """Test ReportEntity."""

    def test_from_report_id(self, django_assert_max_num_queries, deployment_reports):
        """Test ReportEntity factory method "from_report_id"."""
        # pick the id for one of the reports
        report_id = deployment_reports[0].report.id
        deployment_id = deployment_reports[0].id

        with django_assert_max_num_queries(2):
            report = ReportEntity.from_report_id(report_id)
            # ensure products does not trigger another query
            assert isinstance(report.hosts[0].products, set)

        assert isinstance(report, ReportEntity)

        assert report.report_id == report_id
        fingerprint_ids = set(host.id for host in report.hosts)

        fingerprints_from_report = SystemFingerprint.objects.filter(
            deployment_report_id=deployment_id
        )
        assert set(f.id for f in fingerprints_from_report) == fingerprint_ids

    def test_from_report_id_deployment_not_found(self):
        """Check if the proper error is raised."""
        with pytest.raises(DeploymentsReport.DoesNotExist):
            ReportEntity.from_report_id(42)

    def test_from_report_id_fingerprint_not_found(self):
        """Check if the proper error is raised."""
        deployment_report = DeploymentReportFactory(number_of_fingerprints=0)
        with pytest.raises(SystemFingerprint.DoesNotExist):
            ReportEntity.from_report_id(deployment_report.report.id)

    def test_last_discovered_built_from_factory(self, django_assert_num_queries):
        """Test last_discovered property."""
        deployment = DeploymentReportFactory()
        deployment_id = deployment.id
        report_id = deployment.report.id
        # query for deployment report to force only deployment report to be loaded
        DeploymentsReport.objects.get(id=deployment_id)
        report = ReportEntity.from_report_id(report_id)
        with django_assert_num_queries(0):
            assert isinstance(report.last_discovered, datetime)

    def test_last_discovered_initialized(self, django_assert_num_queries):
        """Test last_discovered property with ReportEntity initialized manually."""
        deployment_id = DeploymentReportFactory().id
        # query for deployment report to force only deployment report to be loaded
        deployment_report = DeploymentsReport.objects.get(id=deployment_id)
        report = ReportEntity(
            deployment_report, hosts=deployment_report.system_fingerprints.all()
        )
        with django_assert_num_queries(2):
            assert isinstance(report.last_discovered, datetime)

    def test_canonical_facts_skipping(self, caplog):
        """Test the mechanism for skipping hosts w/o canonical facts."""
        caplog.set_level(logging.WARNING)
        deployment_report = DeploymentReportFactory.create(number_of_fingerprints=1)
        non_canonical_fp = SystemFingerprint.objects.create(
            deployment_report=deployment_report
        )
        assert deployment_report.system_fingerprints.count() == 2
        report_filtered = ReportEntity.from_report_id(deployment_report.report.id)
        assert len(report_filtered.hosts) == 1
        report_unfiltered = ReportEntity.from_report_id(
            deployment_report.report.id, skip_non_canonical=False
        )
        assert len(report_unfiltered.hosts) == 2
        assert (
            caplog.messages[-1]
            == f"Host (fingerprint={non_canonical_fp.id}, name=None) "
            "ignored due to lack of canonical facts."
        )


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
        report = ReportEntity.from_report_id(
            system_fingerprint.deployment_report.report.id
        )
        return report.hosts[0]

    def test_products_not_implemented(self, fingerprint):
        """Ensure only properly initialized host have products."""
        host = HostEntity(fingerprint, last_discovered=None)
        with pytest.raises(NotImplementedError):
            host.products

    @pytest.mark.parametrize(
        "fingerprint,expected_product_names",
        [
            (
                pytest.lazy_fixture("fingerprint_wo_products"),
                set(),
            ),
            (
                pytest.lazy_fixture("fingerprint_with_products"),
                {"JBoss EAP", "UNKOWN PRODUCT"},
            ),
        ],
    )
    def test_products(
        self,
        fingerprint,
        expected_product_names,
    ):
        """Test products properties."""
        host = self.host_init(fingerprint)
        assert host.products == expected_product_names

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
    def test_cores_per_socket(  # noqa: PLR0913
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

    @pytest.mark.parametrize(
        "role, expected_result",
        (
            (
                "Red Hat Enterprise Linux Workstation",
                {"role": "Red Hat Enterprise Linux Workstation"},
            ),
            (
                "Red Hat Enterprise Linux Server",
                {"role": "Red Hat Enterprise Linux Server"},
            ),
            (
                "Red Hat Enterprise Linux Compute Node",
                {"role": "Red Hat Enterprise Linux Compute Node"},
            ),
            ("Red Hat ENterprise", {}),
            ("Workstation", {}),
            ("Enterprise Linux Server", {}),
            (None, {}),
        ),
    )
    def test_role_values(self, mocker, role, expected_result):
        """Test system purpose role logic."""
        mocked_fingerprint = mocker.Mock(system_role=role)
        host = HostEntity(mocked_fingerprint, None)
        assert host.system_purpose == expected_result

    @pytest.mark.parametrize(
        "sla, expected_result",
        (
            ("Premium", {"sla": "Premium"}),
            ("Self-Support", {"sla": "Self-Support"}),
            ("Standard", {"sla": "Standard"}),
            ("Dev-Professional", {}),
            (None, {}),
        ),
    )
    def test_sla_values(self, mocker, sla, expected_result):
        """Test system purpose SLA logic."""
        mocked_fingerprint = mocker.Mock(system_service_level_agreement=sla)
        host = HostEntity(mocked_fingerprint, None)
        assert host.system_purpose == expected_result

    @pytest.mark.parametrize(
        "usage, expected_result",
        (
            ("Development/Test", {"usage": "Development/Test"}),
            ("Production", {"usage": "Production"}),
            ("Disaster Recovery", {"usage": "Disaster Recovery"}),
            ("Development", {}),
            ("prod", {}),
            (None, {}),
        ),
    )
    def test_usage_values(self, mocker, usage, expected_result):
        """Test system purpose usage logic."""
        mocked_fingerprint = mocker.Mock(system_usage_type=usage)
        host = HostEntity(mocked_fingerprint, None)
        assert host.system_purpose == expected_result

    def test_system_purpose(self, mocker):
        """Test system purpose with all possible fields."""
        role = "Red Hat Enterprise Linux Workstation"
        sla = "Premium"
        usage = "Production"
        mocked_fingerprints = mocker.Mock(
            system_role=role,
            system_service_level_agreement=sla,
            system_usage_type=usage,
        )
        expected_result = {"role": role, "sla": sla, "usage": usage}

        host = HostEntity(mocked_fingerprints, None)
        assert host.system_purpose == expected_result

    @pytest.mark.parametrize(
        "ip_addresses, expected_result",
        (
            (["127.0.0.1", "2001:0db8:85a3:0000:0000:8a2e:0370:733"], ["127.0.0.1"]),
            (["random_word", "192.168.1.1"], ["192.168.1.1"]),
            (None, []),
        ),
    )
    def test_ipv4_addresses(self, mocker, ip_addresses, expected_result):
        """Test ipv4_addresses logic."""
        mocked_fingerprint = mocker.Mock(ip_addresses=ip_addresses)
        host = HostEntity(mocked_fingerprint, None)
        assert host.ipv4_addresses == expected_result
        assert not host.ipv6_addresses
