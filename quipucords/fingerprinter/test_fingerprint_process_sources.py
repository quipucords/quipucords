"""Test FingerprintTaskRunner._process_sources."""

import logging

import pytest

from api.models import DetailsReport, ScanJob, ScanTask
from constants import DataSources
from fingerprinter.runner import FingerprintTaskRunner

logger = logging.getLogger(__file__)


@pytest.fixture
def details_report(mocker):
    """Details report patched to contain all possible source types."""
    report = mocker.MagicMock(spec=DetailsReport)
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
        "5 sources to process",
        "PROCESSING Source 1 of 5 - (name=network, type=network, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 network fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=0, satellite=0, openshift=0, ansible=0, total=3)",
        "PROCESSING Source 2 of 5 - (name=vcenter, type=vcenter, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 vcenter fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=0, openshift=0, ansible=0, total=6)",
        "PROCESSING Source 3 of 5 - (name=satellite, type=satellite, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 satellite fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=0, ansible=0, total=9)",
        "PROCESSING Source 4 of 5 - (name=openshift, type=openshift, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 openshift fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=3, ansible=0, total=12)",
        "PROCESSING Source 5 of 5 - (name=ansible, type=ansible, server=<ID>)",
        "SOURCE FINGERPRINTS - 3 ansible fingerprints",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=3, vcenter=3, satellite=3, openshift=3, ansible=3, total=15)",
        "NETWORK DEDUPLICATION by keys ['subscription_manager_id', 'bios_uuid']",
        "NETWORK DEDUPLICATION RESULT - (before=3, after=2)",
        "SATELLITE DEDUPLICATION by keys ['subscription_manager_id']",
        "SATELLITE DEDUPLICATION RESULT - (before=3, after=2)",
        "VCENTER DEDUPLICATION by keys ['vm_uuid']",
        "VCENTER DEDUPLICATION RESULT - (before=3, after=2)",
        "TOTAL FINGERPRINT COUNT - Fingerprints "
        "(network=2, vcenter=2, satellite=2, openshift=3, ansible=3, total=12)",
        "NETWORK and SATELLITE DEDUPLICATION by keys pairs [(network_key, "
        "satellite_key)]=[('subscription_manager_id', 'subscription_manager_id'), "
        "('mac_addresses', 'mac_addresses')]",
        "NETWORK and SATELLITE DEDUPLICATION START COUNT - Fingerprints "
        "(network=2, vcenter=2, satellite=2, openshift=3, ansible=3, total=12)",
        "NETWORK and SATELLITE DEDUPLICATION END COUNT - Fingerprints "
        "(vcenter=2, openshift=3, ansible=3, combined_fingerprints=2, total=10)",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION by keys pairs "
        "[(network_satellite_key, vcenter_key)]=[('bios_uuid', 'vm_uuid'), "
        "('mac_addresses', 'mac_addresses')]",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION by reverse priority keys "
        "(we trust vcenter more than network/satellite): "
        "{'cpu_count', 'infrastructure_type'}",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION START COUNT - Fingerprints "
        "(vcenter=2, openshift=3, ansible=3, combined_fingerprints=2, total=10)",
        "NETWORK-SATELLITE and VCENTER DEDUPLICATION END COUNT - Fingerprints "
        "(openshift=3, ansible=3, combined_fingerprints=2, total=8)",
        "COMBINE with OPENSHIFT+ANSIBLE fingerprints - Fingerprints (total=8)",
    ]


def test_process_sources(
    task_runner: FingerprintTaskRunner, expected_messages, details_report, caplog
):
    """Test FingerprintTaskRunner._process_sources counting mechanism."""
    caplog.set_level(logging.INFO)

    fingerprints = task_runner._process_sources(details_report)  # noqa: W0212
    non_merged_fingerprints = [1, 2, 2]
    # ocp/ansible fingerprints wont be part of deduplication/merging process
    assert fingerprints == [1, 2] + 2 * non_merged_fingerprints
    print("Testing exepected_messages against caplog.records")
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
