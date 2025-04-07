"""Test the aggregate report model generation."""

from datetime import date

import pytest

from api.aggregate_report.model import (
    UNKNOWN,
    AggregateReport,
    build_aggregate_report,
    get_aggregate_report_by_report_id,
    reformat_aggregate_report_to_dict,
)
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
def report_and_expected_aggregate() -> tuple[Report, AggregateReport]:  # noqa: PLR0915
    """
    Build a custom report for testing specific aggregate report use cases.

    As we build the SystemFingerprints and RawFacts (via InspectResultFactory)
    here, we incrementally update values we expect the final generated
    AggregateReport to contain.

    Please read the expected_aggregate updates between objects carefully
    to understand how each new object should affect the end result.
    """
    expected_aggregate = AggregateReport()
    # We construct fingerprints with different dates that should average to this:
    expected_aggregate.system_creation_date_average = date(2024, 4, 1)

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
    expected_aggregate.instances_virtual += 1
    expected_aggregate.socket_pairs += 1
    expected_aggregate.jboss_eap_instances += 1
    expected_aggregate.jboss_eap_cores_virtual += 2
    expected_aggregate.os_by_name_and_version[DEFAULT_RHEL_OS_NAME] = {"9.1": 1}

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
    expected_aggregate.instances_physical += 1
    expected_aggregate.missing_system_purpose += 1
    expected_aggregate.missing_pem_files += 1
    expected_aggregate.socket_pairs += 2
    expected_aggregate.jboss_ws_instances += 1
    expected_aggregate.jboss_ws_cores_physical += 8
    expected_aggregate.os_by_name_and_version[DEFAULT_RHEL_OS_NAME]["9.1"] += 1

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
    expected_aggregate.instances_hypervisor += 1
    expected_aggregate.missing_cpu_core_count += 1
    expected_aggregate.missing_system_purpose += 1
    expected_aggregate.missing_pem_files += 1
    expected_aggregate.socket_pairs += 8
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.os_by_name_and_version[DEFAULT_RHEL_OS_NAME]["9.2"] = 1

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
    expected_aggregate.instances_unknown += 1
    expected_aggregate.missing_cpu_core_count += 1
    expected_aggregate.missing_cpu_socket_count += 1
    expected_aggregate.missing_name += 1
    expected_aggregate.missing_pem_files += 1
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.missing_system_purpose += 1
    expected_aggregate.os_by_name_and_version[DEFAULT_RHEL_OS_NAME][UNKNOWN] = 1

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
    expected_aggregate.instances_unknown += 1
    expected_aggregate.missing_name += 1
    expected_aggregate.missing_cpu_socket_count += 1
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.os_by_name_and_version[UNKNOWN] = {UNKNOWN: 1}

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
    expected_aggregate.instances_virtual += 1
    expected_aggregate.missing_cpu_socket_count += 1
    expected_aggregate.openshift_cores += 32
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.os_by_name_and_version[UNKNOWN]["NCC-1701"] = 1

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
    expected_aggregate.instances_not_redhat += 1
    expected_aggregate.os_by_name_and_version["LCARS"] = {"NCC-1701-D": 1}

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
    expected_aggregate.instances_virtual += 1
    expected_aggregate.missing_name += 1
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.socket_pairs += 512
    expected_aggregate.vmware_hosts += 1
    expected_aggregate.vmware_vms += 1
    expected_aggregate.os_by_name_and_version[UNKNOWN][UNKNOWN] += 1

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
    expected_aggregate.instances_virtual += 1
    expected_aggregate.missing_cpu_socket_count += 1
    expected_aggregate.missing_name += 1
    expected_aggregate.missing_system_creation_date += 1
    expected_aggregate.vmware_vms += 1
    expected_aggregate.os_by_name_and_version[UNKNOWN][UNKNOWN] += 1

    expected_aggregate.vmware_vm_to_host_ratio = 2.0  # (2/1)

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
    expected_aggregate.inspect_result_status_unknown += 1
    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={
            "hosts": [{"name": "b"}, {"name": "c"}, {"name": "b"}],
            "jobs": {"unique_hosts": ["c", "d", "e", "f"]},
        },
        status=InspectResult.SUCCESS,  # inspect_result_status_success++
    )
    expected_aggregate.inspect_result_status_success += 1
    expected_aggregate.ansible_hosts_all = 6  # {"a", "b", "c", "d", "e", "f"}
    expected_aggregate.ansible_hosts_in_database = 3  # {"a", "b", "c"}
    expected_aggregate.ansible_hosts_in_jobs = 4  # {"c", "d", "e", "f"}

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
    expected_aggregate.inspect_result_status_success += 1
    expected_aggregate.openshift_cluster_instances += 1
    expected_aggregate.openshift_operators_by_kind["unknown"] = 1
    expected_aggregate.openshift_operators_by_kind["type1"] = 2
    expected_aggregate.openshift_operators_by_kind["type2"] = 3
    expected_aggregate.openshift_operators_by_name["unknown"] = 3
    expected_aggregate.openshift_operators_by_name["name1"] = 1
    expected_aggregate.openshift_operators_by_name["name2"] = 2

    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={"node": {"kind": "node"}},  # openshift_node_instances++
        status=InspectResult.FAILED,  # inspect_result_status_failed++
    )
    expected_aggregate.inspect_result_status_failed += 1
    expected_aggregate.openshift_node_instances += 1

    InspectResultFactory(
        inspect_group=inspect_group,
        with_raw_facts={"asdf": {}},  # not a cluster or node? no effect.
        status=InspectResult.UNREACHABLE,  # inspect_result_status_unreachable++
    )
    expected_aggregate.inspect_result_status_unreachable += 1

    return report, expected_aggregate


@pytest.mark.django_db
def test_build_aggregate_report_system_fingerprint(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test build_aggregate_report using generated Report, SystemFingerprints, etc."""
    report, expected_aggregate_report = report_and_expected_aggregate
    aggregated = build_aggregate_report(report.id)
    assert aggregated is not None
    assert reformat_aggregate_report_to_dict(
        aggregated
    ) == reformat_aggregate_report_to_dict(expected_aggregate_report)


@pytest.mark.django_db
def test_get_aggregate_report_by_report_id(
    report_and_expected_aggregate: tuple[Report, AggregateReport],
):
    """Test that if the Report exists, a proper report is generated."""
    report, expected_aggregate_report = report_and_expected_aggregate
    aggregate = get_aggregate_report_by_report_id(report.id)
    assert aggregate == reformat_aggregate_report_to_dict(expected_aggregate_report)


@pytest.mark.django_db
def test_get_aggregate_report_by_report_id_not_found():
    """Test that if the Report does not exist, None report is generated."""
    assert get_aggregate_report_by_report_id(-1) is None
