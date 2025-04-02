"""Test the scanner.network.inspect.ConnectResultStore class."""

import pytest

from api.connresult.model import SystemConnectionResult
from api.scantask.model import ScanTask
from scanner.network.inspect import ConnectResultStore
from tests.factories import ScanFactory, ScanTaskFactory, SourceFactory

pytestmark = pytest.mark.django_db  # all tests here require the database


def test_result_store_when_host_address_is_unreachable(faker):
    """Test record_result when the host address is unreachable."""
    host_address = faker.ipv4()
    source = SourceFactory(hosts=[host_address])
    credential = source.credentials.first()
    scan = ScanFactory(sources=[source])
    scan_job = scan.most_recent_scanjob
    scan_job.sources.add(source)
    # TODO replace with inspect type
    scan_task = ScanTaskFactory(
        job=scan_job, scan_type=ScanTask.SCAN_TYPE_CONNECT, source=source
    )

    result_store = ConnectResultStore(scan_task)

    assert result_store.remaining_hosts() == [host_address]
    assert result_store.scan_task.systems_count == 1
    assert result_store.scan_task.systems_scanned == 0
    assert result_store.scan_task.systems_failed == 0

    result_store.record_result(
        host_address, source, credential, SystemConnectionResult.UNREACHABLE
    )

    assert result_store.remaining_hosts() == []
    assert result_store.scan_task.systems_count == 1
    assert result_store.scan_task.systems_scanned == 0
    assert result_store.scan_task.systems_unreachable == 1


def test_result_store_with_multiple_conditions(faker):
    """
    Test record_result with three addresses, each with a different result.

    The setup for this test requires definition of a scan where the related
    source has three host addresses. The test logic simulates a scan run in which:

    - the first host address succeeds
    - the second fails due to missing credentials
    - the third fails due to some other specified error
    """
    host_addresses = [faker.ipv4(), faker.ipv4(), faker.ipv4()]
    source = SourceFactory(hosts=host_addresses)
    credential = source.credentials.first()
    scan = ScanFactory(sources=[source])
    scan_job = scan.most_recent_scanjob
    scan_job.sources.add(source)
    # TODO replace with inspect type
    scan_task = ScanTaskFactory(
        job=scan_job, scan_type=ScanTask.SCAN_TYPE_CONNECT, source=source
    )

    result_store = ConnectResultStore(scan_task)
    assert len(result_store.remaining_hosts()) == len(host_addresses)
    assert result_store.scan_task.systems_count == 3
    assert result_store.scan_task.systems_scanned == 0
    assert result_store.scan_task.systems_failed == 0

    host = host_addresses.pop()
    result_store.record_result(host, source, credential, SystemConnectionResult.SUCCESS)

    assert len(result_store.remaining_hosts()) == len(host_addresses)
    assert result_store.scan_task.systems_count == 3
    assert result_store.scan_task.systems_scanned == 1
    assert result_store.scan_task.systems_failed == 0

    host = host_addresses.pop()
    # Check failure without cred
    result_store.record_result(host, source, None, SystemConnectionResult.FAILED)
    assert len(result_store.remaining_hosts()) == len(host_addresses)
    assert result_store.scan_task.systems_count == 3
    assert result_store.scan_task.systems_scanned == 1
    assert result_store.scan_task.systems_failed == 1

    host = host_addresses.pop()
    # Check failure with cred
    result_store.record_result(host, source, credential, SystemConnectionResult.FAILED)
    assert len(result_store.remaining_hosts()) == len(host_addresses)
    assert result_store.scan_task.systems_count == 3
    assert result_store.scan_task.systems_scanned == 1
    assert result_store.scan_task.systems_failed == 2
