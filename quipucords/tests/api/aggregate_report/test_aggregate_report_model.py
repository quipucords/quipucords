"""Test the aggregate report model generation."""

from collections import defaultdict
from datetime import date, timedelta

import pytest

from api.aggregate_report.model import (
    UNKNOWN,
    AggregateReport,
    build_aggregate_report,
    get_aggregate_report_by_report_id,
)
from api.aggregate_report.serializer import AggregateReportSerializer
from api.deployments_report.model import DeploymentsReport, Product, SystemFingerprint
from api.inspectresult.model import InspectResult
from api.report.model import Report
from constants import DataSources
from fingerprinter import jboss_eap, jboss_web_server
from tests.factories import (
    DeploymentReportFactory,
    InspectGroupFactory,
    InspectResultFactory,
    ReportFactory,
    SystemFingerprintFactory,
)
from tests.utils.raw_facts_generator import DEFAULT_RHEL_OS_NAME


@pytest.fixture
def expected_aggregate() -> dict:
    """Return an AggregateReport dictionary with defaults."""
    return {
        "results": {
            "ansible_hosts_all": 0,
            "ansible_hosts_in_database": 0,
            "ansible_hosts_in_jobs": 0,
            "instances_hypervisor": 0,
            "instances_not_redhat": 0,
            "instances_physical": 0,
            "instances_unknown": 0,
            "instances_virtual": 0,
            "jboss_eap_cores_physical": 0.0,
            "jboss_eap_cores_virtual": 0.0,
            "jboss_eap_instances": 0,
            "jboss_ws_cores_physical": 0.0,
            "jboss_ws_cores_virtual": 0.0,
            "jboss_ws_instances": 0,
            "openshift_cores": 0,
            "openshift_operators_by_name": {},
            "openshift_operators_by_kind": {},
            "os_by_name_and_version": {
                DEFAULT_RHEL_OS_NAME: defaultdict(int),
                UNKNOWN: defaultdict(int),
                "LCARS": defaultdict(int),
            },
            "socket_pairs": 0,
            "system_creation_date_average": None,
            "vmware_hosts": 0,
            "vmware_vm_to_host_ratio": 0.0,
            "vmware_vms": 0,
            "openshift_cluster_instances": 0,
            "openshift_node_instances": 0,
        },
        "diagnostics": {
            "inspect_result_status_failed": 0,
            "inspect_result_status_success": 0,
            "inspect_result_status_unknown": 0,
            "inspect_result_status_unreachable": 0,
            "missing_cpu_core_count": 0,
            "missing_cpu_socket_count": 0,
            "missing_name": 0,
            "missing_pem_files": 0,
            "missing_system_creation_date": 0,
            "missing_system_purpose": 0,
        },
    }


@pytest.fixture
def report_and_expected_aggregate(expected_aggregate) -> tuple[Report, dict]:  # noqa: PLR0915
    """
    Build a custom report for testing specific aggregate report use cases.

    As we build the SystemFingerprints and RawFacts (via InspectResultFactory)
    here, we incrementally update values we expect the final generated
    AggregateReport to contain.

    Please read the expected_aggregate updates between objects carefully
    to understand how each new object should affect the end result.
    """
    results = expected_aggregate["results"]
    diagnostics = expected_aggregate["diagnostics"]
    os_by_name_and_version = results["os_by_name_and_version"]

    # We construct fingerprints with different dates that should average to this:
    results["system_creation_date_average"] = str(date(2024, 4, 1))

    source_network = {"source_type": DataSources.NETWORK}
    source_ansible = {"source_type": DataSources.ANSIBLE}
    source_openshift = {"source_type": DataSources.OPENSHIFT}
    source_vcenter = {"source_type": DataSources.VCENTER}
    # Note DataSources.SATELLITE and DataSources.RHACS are not uniquely
    # interesting enough for the aggregate report to warrant additional
    # custom test fingerprints/facts objects here.

    deployments_report: DeploymentsReport = DeploymentReportFactory(
        report=None,
        number_of_fingerprints=0,  # 0 so we can define them all below
    )

    # virtual RHEL 9.1 w/ JBoss EAP
    fingerprint = SystemFingerprintFactory(
        os_version="9.1",
        infrastructure_type=SystemFingerprint.VIRTUALIZED,  # instances_virtual++
        deployment_report=deployments_report,
        cpu_count=None,  # cpu_count is only relevant for openshift sources
        cpu_core_count=2,
        cpu_socket_count=1,  # socket_pairs += 1
        system_purpose={"These": "values"},
        redhat_certs=["do", "not", "matter."],
        sources=[source_network],
        system_creation_date=date(2024, 3, 31),
    )
    Product.objects.create(
        name=jboss_eap.PRODUCT, presence=Product.PRESENT, fingerprint=fingerprint
    )  # jboss_eap_instances++, jboss_eap_cores_virtual += 2
    results["instances_virtual"] += 1
    results["socket_pairs"] += 1
    results["jboss_eap_instances"] += 1
    results["jboss_eap_cores_virtual"] += 2
    os_by_name_and_version[DEFAULT_RHEL_OS_NAME] = {"9.1": 1}

    # physical RHEL 9.1 w/ JBoss WS
    fingerprint = SystemFingerprintFactory(
        os_version="9.1",  # same as previous fingerprint os_version
        infrastructure_type=SystemFingerprint.BARE_METAL,  # instances_physical++
        deployment_report=deployments_report,
        cpu_count=None,  # cpu_count is only relevant for openshift sources
        cpu_core_count=8,
        cpu_socket_count=4,  # socket_pairs += 2
        system_purpose=None,  # missing_system_purpose++
        redhat_certs=None,  # missing_pem_files++
        sources=[source_network],
        system_creation_date=date(2024, 4, 2),
    )
    Product.objects.create(
        name=jboss_web_server.PRODUCT, presence=Product.PRESENT, fingerprint=fingerprint
    )  # jboss_ws_instances++, jboss_ws_cores_physical += 8
    results["instances_physical"] += 1
    diagnostics["missing_system_purpose"] += 1
    diagnostics["missing_pem_files"] += 1
    results["socket_pairs"] += 2
    results["jboss_ws_instances"] += 1
    results["jboss_ws_cores_physical"] += 8
    os_by_name_and_version[DEFAULT_RHEL_OS_NAME]["9.1"] += 1

    # hypervisor RHEL 9.2
    SystemFingerprintFactory(
        os_version="9.2",  # different from previous fingerprint os_version
        infrastructure_type=SystemFingerprint.HYPERVISOR,  # instances_hypervisor++
        deployment_report=deployments_report,
        cpu_count=None,  # cpu_count is only relevant for openshift sources
        cpu_core_count=None,  # missing_cpu_core_count++
        cpu_socket_count=16,  # socket_pairs += 8
        system_purpose=None,  # missing_system_purpose++
        redhat_certs=None,  # missing_pem_files++
        sources=[source_network],
        system_creation_date=None,  # missing_system_creation_date++
    )
    results["instances_hypervisor"] += 1
    diagnostics["missing_cpu_core_count"] += 1
    diagnostics["missing_system_purpose"] += 1
    diagnostics["missing_pem_files"] += 1
    results["socket_pairs"] += 8
    diagnostics["missing_system_creation_date"] += 1
    os_by_name_and_version[DEFAULT_RHEL_OS_NAME]["9.2"] = 1

    # RHEL with several important facts not set ("missing")
    SystemFingerprintFactory(
        name=None,  # missing_name++
        os_version=None,
        infrastructure_type=SystemFingerprint.UNKNOWN,  # instances_unknown++
        deployment_report=deployments_report,
        cpu_count=None,  # cpu_count is only relevant for openshift sources
        cpu_core_count=None,  # missing_cpu_core_count++
        cpu_socket_count=None,  # missing_cpu_socket_count++
        system_purpose=None,  # missing_system_purpose++
        redhat_certs=None,  # missing_pem_files++
        sources=[source_network],
        system_creation_date=None,  # missing_system_creation_date++
    )
    results["instances_unknown"] += 1
    diagnostics["missing_cpu_core_count"] += 1
    diagnostics["missing_cpu_socket_count"] += 1
    diagnostics["missing_name"] += 1
    diagnostics["missing_pem_files"] += 1
    diagnostics["missing_system_creation_date"] += 1
    diagnostics["missing_system_purpose"] += 1
    os_by_name_and_version[DEFAULT_RHEL_OS_NAME][UNKNOWN] = 1

    # largely unknown system found via ansible
    SystemFingerprintFactory(
        os_version=None,
        os_name=None,
        name=None,  # missing_name++
        infrastructure_type=SystemFingerprint.UNKNOWN,  # instances_unknown++
        deployment_report=deployments_report,
        cpu_count=None,  # cpu_count is only relevant for openshift sources
        cpu_core_count=None,  # ansible has no effect on missing_cpu_core_count
        cpu_socket_count=None,  # missing_cpu_socket_count++
        sources=[source_ansible],
        system_creation_date=None,  # missing_system_creation_date++
    )
    results["instances_unknown"] += 1
    diagnostics["missing_name"] += 1
    diagnostics["missing_cpu_socket_count"] += 1
    diagnostics["missing_system_creation_date"] += 1
    os_by_name_and_version[UNKNOWN] = {UNKNOWN: 1}

    # openshift with mysterious OS identifier
    SystemFingerprintFactory(
        os_name=None,
        os_version="NCC-1701",
        infrastructure_type=SystemFingerprint.VIRTUALIZED,  # instances_virtual++
        deployment_report=deployments_report,
        cpu_count=32,  # cpu_count is only relevant for openshift sources
        cpu_socket_count=None,  # missing_cpu_socket_count++
        cpu_core_count=64,  # openshift_cores += 32
        sources=[source_openshift],
        system_creation_date=None,  # missing_system_creation_date++
    )
    results["instances_virtual"] += 1
    diagnostics["missing_cpu_socket_count"] += 1
    results["openshift_cores"] += 32
    diagnostics["missing_system_creation_date"] += 1
    os_by_name_and_version[UNKNOWN]["NCC-1701"] = 1

    # Not-RHEL system found by network scan
    # Unlike the openshift one above, this one DOES NOT increment counters,
    # but we do track its OS name and version anyway.
    SystemFingerprintFactory(
        os_name="LCARS",
        os_version="NCC-1701-D",
        is_redhat=False,
        infrastructure_type=SystemFingerprint.VIRTUALIZED,
        deployment_report=deployments_report,
        cpu_count=128,
        cpu_core_count=256,
        cpu_socket_count=512,
        sources=[source_network],
        system_creation_date=date(1970, 1, 1),
    )
    results["instances_not_redhat"] += 1
    os_by_name_and_version["LCARS"] = {"NCC-1701-D": 1}

    # os_name, os_version, and name are frequently blank in real vcenter scans.
    # We set them to None here only to mimic this IRL behavior.
    SystemFingerprintFactory(
        os_name=None,
        os_version=None,
        name=None,  # missing_name++
        infrastructure_type=SystemFingerprint.VIRTUALIZED,
        deployment_report=deployments_report,
        cpu_count=None,
        cpu_core_count=None,
        cpu_socket_count=1024,  # socket_pairs += 512
        sources=[source_vcenter],
        vm_cluster="vmware_host1",
        virtual_host_uuid="vmware_vm1",
    )
    results["instances_virtual"] += 1
    diagnostics["missing_name"] += 1
    diagnostics["missing_system_creation_date"] += 1
    results["socket_pairs"] += 512
    results["vmware_hosts"] += 1
    results["vmware_vms"] += 1
    os_by_name_and_version[UNKNOWN][UNKNOWN] += 1

    # os_name, os_version, and name are frequently blank in real vcenter scans.
    # We set them to None here only to mimic this IRL behavior.
    SystemFingerprintFactory(
        os_name=None,
        os_version=None,
        name=None,  # missing_name++
        infrastructure_type=SystemFingerprint.VIRTUALIZED,
        deployment_report=deployments_report,
        cpu_count=None,
        cpu_core_count=None,
        cpu_socket_count=None,  # missing_cpu_socket_count++
        sources=[source_vcenter],
        vm_cluster="vmware_host1",  # same as previous fingerprint
        virtual_host_uuid="vmware_vm2",  # different from previous fingerprint
    )
    results["instances_virtual"] += 1
    diagnostics["missing_cpu_socket_count"] += 1
    diagnostics["missing_name"] += 1
    diagnostics["missing_system_creation_date"] += 1
    results["vmware_vms"] += 1
    os_by_name_and_version[UNKNOWN][UNKNOWN] += 1

    results["vmware_vm_to_host_ratio"] = 2.0  # (2/1)

    report: Report = ReportFactory(
        deployment_report=deployments_report, generate_raw_facts=False
    )
    scan_task = ReportFactory.get_or_create_inspect_task(report)

    # Ansible-specific raw facts
    inspect_group = InspectGroupFactory(source_type=DataSources.ANSIBLE)
    inspect_group.tasks.add(scan_task)
    report.inspect_groups.add(inspect_group)
    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={
            "hosts": [{"name": "a"}, {}, {"name": None, "jobs": {}}],
            "jobs": {"unique_hosts": ["d", "d", "d"]},
        },
        # because status=None by default, inspect_result_status_unknown++
    )
    diagnostics["inspect_result_status_unknown"] += 1
    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={
            "hosts": [{"name": "b"}, {"name": "c"}, {"name": "b"}],
            "jobs": {"unique_hosts": ["c", "d", "e", "f"]},
        },
        status=InspectResult.SUCCESS,  # inspect_result_status_success++
    )
    diagnostics["inspect_result_status_success"] += 1
    results["ansible_hosts_all"] = 6  # {"a", "b", "c", "d", "e", "f"}
    results["ansible_hosts_in_database"] = 3  # {"a", "b", "c"}
    results["ansible_hosts_in_jobs"] = 4  # {"c", "d", "e", "f"}

    # OpenShift-specific raw facts
    inspect_group = InspectGroupFactory(source_type=DataSources.OPENSHIFT)
    inspect_group.tasks.add(scan_task)
    report.inspect_groups.add(inspect_group)
    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={
            "cluster": {"kind": "cluster"},  # openshift_cluster_instances++
            "operators": [
                {"kind": "type1", "name": "name1"},
                {"kind": "type2"},
                {"kind": "type1", "name": "name2"},
                {},
                {"kind": "type2", "name": "name2"},
                {"kind": "type2"},
            ],  # openshift_operators_by_kind[...]++
        },
        status=InspectResult.SUCCESS,  # inspect_result_status_success++
    )
    diagnostics["inspect_result_status_success"] += 1
    results["openshift_cluster_instances"] += 1
    results["openshift_operators_by_kind"] = {
        "unknown": 1,
        "type1": 2,
        "type2": 3,
    }
    results["openshift_operators_by_name"] = {
        "unknown": 3,
        "name1": 1,
        "name2": 2,
    }

    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={"node": {"kind": "node"}},  # openshift_node_instances++
        status=InspectResult.FAILED,  # inspect_result_status_failed++
    )
    diagnostics["inspect_result_status_failed"] += 1
    results["openshift_node_instances"] += 1

    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={"asdf": {}},  # not a cluster or node? no effect.
        status=InspectResult.UNREACHABLE,  # inspect_result_status_unreachable++
    )
    diagnostics["inspect_result_status_unreachable"] += 1

    return report, dict(expected_aggregate)


@pytest.mark.django_db
def test_build_aggregate_report_system_fingerprint(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test build_aggregate_report using generated Report, SystemFingerprints, etc."""
    report, expected_aggregate_report = report_and_expected_aggregate
    aggregated = build_aggregate_report(report.id)
    assert aggregated is not None
    assert (
        AggregateReportSerializer(instance=aggregated).data == expected_aggregate_report
    )


@pytest.mark.django_db
def test_build_aggregate_report_already_exists(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """
    Test build_aggregate_report destroys and recalculates if it needs update.

    This logic should only be triggered if the related Report object has been modified
    more recently than the AggregateReport object. That tends to happen when we update
    on-disk cache files for the reports and write the file path into the Report model.
    """
    report, expected_aggregate_report = report_and_expected_aggregate
    first_aggregated = build_aggregate_report(report.id)
    first_aggregated_id = first_aggregated.id

    report.updated_at = report.updated_at + timedelta(seconds=1)
    report.save()
    second_aggregated = build_aggregate_report(report.id)
    second_aggregated_id = second_aggregated.id

    assert first_aggregated_id != second_aggregated_id
    with pytest.raises(AggregateReport.DoesNotExist):
        first_aggregated.refresh_from_db()


@pytest.mark.django_db
def test_get_aggregate_report_by_report_id(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test that if the Report exists, a proper report is generated."""
    report, expected_aggregate_report = report_and_expected_aggregate
    aggregate = get_aggregate_report_by_report_id(report.id)
    assert (
        AggregateReportSerializer(instance=aggregate).data == expected_aggregate_report
    )


@pytest.mark.django_db
def test_get_aggregate_report_by_report_id_generated_db_record(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test that if the aggregate report is obtained, the DB Record exists."""
    report, expected_aggregate_report = report_and_expected_aggregate
    _aggregate = get_aggregate_report_by_report_id(report.id)
    assert AggregateReport.objects.filter(report_id=report.id).exists()


@pytest.mark.django_db
def test_report_deletes_delete_aggregate(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test that if the Report is deleted, the aggregate DB Record is also deleted."""
    report, expected_aggregate_report = report_and_expected_aggregate
    _aggregate = get_aggregate_report_by_report_id(report.id)
    assert AggregateReport.objects.filter(report_id=report.id).exists()
    report.delete()
    assert not AggregateReport.objects.filter(report_id=report.id).exists()


@pytest.mark.django_db
def test_get_aggregate_report_by_report_id_not_found():
    """Test that if the Report does not exist, None report is generated."""
    assert get_aggregate_report_by_report_id(-1) is None
