"""Test FingerprintTaskRunner._process_sources."""

import logging

import pytest

from api.models import InspectGroup, InspectResult, Report, ScanJob, ScanTask
from constants import DataSources
from fingerprinter.runner import FingerprintTaskRunner
from tests.factories import InspectResultFactory, ReportFactory, ScanTaskFactory

logger = logging.getLogger(__file__)


@pytest.fixture
def report(mocker):
    """Report patched to contain all possible source types."""
    report = mocker.MagicMock(spec=Report)
    report.sources = [
        {
            "source_type": source_type,
            "source_name": source_type,
            "server_id": "<ID>",
        }
        for source_type in DataSources.values
    ]
    return report


@pytest.fixture
def scan_task(mocker):
    """Scan task mocked to only log messages."""

    def _log_message(message, log_level=logging.INFO, **kwargs):
        logger.log(level=log_level, msg=message)

    patched_scan_task = mocker.MagicMock(spec=ScanTask)
    patched_scan_task.log_message.side_effect = _log_message
    return patched_scan_task


@pytest.fixture
def task_runner(mocker, scan_task):
    """
    Fingerprint task runner patched for controlled processing of fingerprints.

    The actual fingerprinting process is patched to handle "fake" fingerprints as
    follows:
        - (process_source): start with 3 fingerprints per source type
        - (deduplication): will always result in 2 fingerprints
        - (merging): will also result in 2 fingerprints
        - (post_process): ignored.
    """

    def _process_source(*args, **kwargs):
        return [1, 2, 2]

    def _remove_duplicate_fp(*args, **kwargs):
        return [1, 2]

    def _merge_fps(*args, **kwargs):
        return 2, [1, 2]

    mocker.patch.object(
        FingerprintTaskRunner,
        "_process_source",
        side_effect=_process_source,
    )
    mocker.patch.object(
        FingerprintTaskRunner,
        "_remove_duplicate_fingerprints",
        side_effect=_remove_duplicate_fp,
    )
    mocker.patch.object(
        FingerprintTaskRunner,
        "_merge_fingerprints_from_source_types",
        side_effect=_merge_fps,
    )
    mocker.patch.object(FingerprintTaskRunner, "_post_process_merged_fingerprints")
    scan_job = mocker.MagicMock(spec=ScanJob)
    return FingerprintTaskRunner(scan_job=scan_job, scan_task=scan_task)


@pytest.fixture
def expected_messages():
    """Messages expected when mocked FingerprintTaskRunner is executed."""
    return [
        "6 sources to process",
        "PROCESSING Source 1 of 6 - (name=network, type=network, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 network fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=0, satellite=0, openshift=0, ansible=0, rhacs=0, total=3)",
        "PROCESSING Source 2 of 6 - (name=vcenter, type=vcenter, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 vcenter fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=0, openshift=0, ansible=0, rhacs=0, total=6)",
        "PROCESSING Source 3 of 6 - (name=satellite, type=satellite, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 satellite fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=0, ansible=0, rhacs=0, total=9)",
        "PROCESSING Source 4 of 6 - (name=openshift, type=openshift, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 openshift fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=3, ansible=0, rhacs=0, total=12)",  # noqa: E501
        "PROCESSING Source 5 of 6 - (name=ansible, type=ansible, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 ansible fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=3, ansible=3, rhacs=0, total=15)",  # noqa: E501
        "PROCESSING Source 6 of 6 - (name=rhacs, type=rhacs, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 rhacs fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=3, ansible=3, rhacs=3, total=18)",  # noqa: E501
        "NETWORK DEDUPLICATION by keys ['subscription_manager_id', 'bios_uuid']",
        "NETWORK DEDUPLICATION RESULT - (before=3, after=2)",
        "SATELLITE DEDUPLICATION by keys ['subscription_manager_id']",
        "SATELLITE DEDUPLICATION RESULT - (before=3, after=2)",
        "VCENTER DEDUPLICATION by keys ['vm_uuid']",
        "VCENTER DEDUPLICATION RESULT - (before=3, after=2)",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=2, vcenter=2, satellite=2, openshift=3, ansible=3, rhacs=3, total=15)",  # noqa: E501
        "NETWORK and SATELLITE DEDUPLICATION by keys pairs [(network_key, "
        "satellite_key)]=[('subscription_manager_id', 'subscription_manager_id'), "
        "('mac_addresses', 'mac_addresses')]",
        "NETWORK and SATELLITE DEDUPLICATION START COUNT - Fingerprints "
        "(network=2, vcenter=2, satellite=2, openshift=3, ansible=3, rhacs=3, total=15)",  # noqa: E501
        "NETWORK and SATELLITE DEDUPLICATION END COUNT - Fingerprints "
        "(vcenter=2, openshift=3, ansible=3, rhacs=3, combined_fingerprints=2, total=13)",  # noqa: E501
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION by keys pairs "
        "[(network_satellite_key, vcenter_key)]=[('bios_uuid', 'vm_uuid'), "
        "('mac_addresses', 'mac_addresses')]",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION by reverse priority keys "
        "(we trust vcenter more than network/satellite): "
        "('cpu_count', 'infrastructure_type')",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION START COUNT - Fingerprints "
        "(vcenter=2, openshift=3, ansible=3, rhacs=3, combined_fingerprints=2, total=13)",  # noqa: E501
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION END COUNT - Fingerprints "
        "(openshift=3, ansible=3, rhacs=3, combined_fingerprints=2, total=11)",
        "COMBINE with OPENSHIFT+ANSIBLE+RHACS fingerprints - Fingerprints (total=11)",
    ]


def test_merge_fingerprints(
    task_runner: FingerprintTaskRunner, expected_messages, report, caplog
):
    """Test FingerprintTaskRunner._process_sources counting mechanism."""
    caplog.set_level(logging.INFO)

    fingerprints = task_runner._process_sources(report)  # noqa: W0212
    non_merged_fingerprints = [1, 2, 2]
    # ocp/ansible/rhacs fingerprints wont be part of deduplication/merging process
    assert fingerprints == [1, 2] + 3 * non_merged_fingerprints
    assert [rec.message for rec in caplog.records] == expected_messages


@pytest.mark.parametrize("data_source", DataSources.values)
def test_process_facts_for_datasource(
    task_runner: FingerprintTaskRunner, data_source, mocker
):
    """Test FingerprintTaskRunner.process_facts_for_datasource."""
    mocker.patch.object(
        task_runner, "_add_fact_to_fingerprint", side_effect=RuntimeError("STOP!!!")
    )
    # if the appropriate method is implemented, our error shall be raised.
    with pytest.raises(RuntimeError, match="STOP!!!"):
        task_runner.process_facts_for_datasource(data_source, {}, {})


@pytest.mark.django_db
def test_process_sources():
    """Test FingerprintTaskRunner._process_sources against a report with raw data."""
    report = ReportFactory(generate_raw_facts=True)
    # add a fact-less InspectResult to reproduce issues with failed systems
    inspect_group = InspectGroup.objects.first()
    InspectResultFactory(inspect_group=inspect_group, status=InspectResult.UNREACHABLE)
    task = ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, job=report.scanjob)
    fingerprint_runner = FingerprintTaskRunner(report.scanjob, task)
    fingerprints = fingerprint_runner._process_sources(report)
    number_of_systems = InspectResult.objects.filter(
        inspect_group__tasks__job=report.scanjob
    ).count()
    number_of_ocp_clusters = InspectGroup.objects.filter(
        tasks__job=report.scanjob,
        source_type=DataSources.OPENSHIFT.value,
    ).count()
    # ignore ocp clusters (as they are not part of deployments) and the failed system
    expected_number_of_fingerprints = number_of_systems - number_of_ocp_clusters - 1
    assert len(fingerprints) == expected_number_of_fingerprints
