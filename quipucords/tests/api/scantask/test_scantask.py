"""Test the ScanTask model and serializer."""

from datetime import datetime
from unittest.mock import patch

import pytest

from api import messages
from api.inspectresult.model import InspectResult, RawFact
from api.models import Credential, Scan, ScanJob, ScanTask, Source
from api.serializers import ScanTaskSerializer
from tests.factories import InspectGroupFactory, InspectResultFactory, ScanTaskFactory


@pytest.fixture
def credential() -> Credential:
    """Create a Credential instance for tests."""
    return Credential.objects.create(
        name="cred1",
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
    )


@pytest.fixture
def source(credential: Credential) -> Source:
    """Create a Source instance for tests."""
    _source = Source.objects.create(name="source1", source_type="network", port=22)
    _source.credentials.add(credential)
    return _source


@pytest.fixture
def scan(source: Source) -> Scan:
    """Create a Scan instance for tests."""
    _scan = Scan.objects.create(name="scan_name", scan_type=ScanTask.SCAN_TYPE_CONNECT)
    _scan.sources.add(source)
    return _scan


@pytest.fixture
def scan_job(scan: Scan) -> ScanJob:
    """Create a ScanJob instance for tests."""
    return ScanJob.objects.create(scan=scan)


@pytest.mark.django_db
class TestScanTask:
    """Test the basic ScanJob infrastructure."""

    def test_successful_create(self, scan_job, source):
        """Create a scan task and serialize it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        serializer = ScanTaskSerializer(task)
        json_task = serializer.data
        expected = {
            "sequence_number": 0,
            "source": source.id,
            "scan_type": ScanTask.SCAN_TYPE_CONNECT,
            "status": "pending",
            "status_message": messages.ST_STATUS_MSG_PENDING,
            "systems_count": 0,
            "systems_scanned": 0,
            "systems_failed": 0,
            "systems_unreachable": 0,
        }
        assert expected == json_task

    def test_successful_start(self, scan_job, source):
        """Create a scan task and start it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        start_time = datetime.utcnow()
        task.status_start()
        assert messages.ST_STATUS_MSG_RUNNING == task.status_message
        assert task.status == ScanTask.RUNNING
        assert start_time.replace(microsecond=0) == task.start_time.replace(
            microsecond=0
        )

    def test_successful_restart(self, scan_job, source):
        """Create a scan task and restart it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.status_restart()
        assert messages.ST_STATUS_MSG_RESTARTED == task.status_message
        assert task.status == ScanTask.PENDING

    def test_successful_pause(self, scan_job, source):
        """Create a scan task and status_pause it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.status_pause()
        assert messages.ST_STATUS_MSG_PAUSED == task.status_message
        assert task.status == ScanTask.PAUSED

    def test_successful_cancel(self, scan_job, source):
        """Create a scan task and cancel it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        end_time = datetime.utcnow()
        task.status_cancel()
        assert messages.ST_STATUS_MSG_CANCELED == task.status_message
        assert task.status == ScanTask.CANCELED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

    def test_successful_complete(self, scan_job, source):
        """Create a scan task and complete it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        end_time = datetime.utcnow()
        task.status_complete("great")
        assert "great" == task.status_message
        assert task.status == ScanTask.COMPLETED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

    def test_scantask_fail(self, scan_job, source):
        """Create a scan task and fail it."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        msg = "Test Fail."
        end_time = datetime.utcnow()
        task.status_fail(msg)
        assert msg == task.status_message
        assert task.status == ScanTask.FAILED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

    def test_scantask_increment(self, scan_job, source):
        """Test scan task increment feature."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.increment_stats(
            "foo",
            increment_sys_count=True,
            increment_sys_scanned=True,
            increment_sys_failed=True,
            increment_sys_unreachable=True,
        )
        assert 1 == task.systems_count
        assert 1 == task.systems_scanned
        assert 1 == task.systems_failed
        assert 1 == task.systems_unreachable
        task.increment_stats(
            "foo",
            increment_sys_count=True,
            increment_sys_scanned=True,
            increment_sys_failed=True,
            increment_sys_unreachable=True,
        )
        assert 2 == task.systems_count
        assert 2 == task.systems_scanned
        assert 2 == task.systems_failed
        assert 2 == task.systems_unreachable

    def test_scantask_increment_stats_multiple_in_parallel(self, scan_job, source):
        """Test scan task increment two instances in parallel.

        This is a special case test to help ensure that increment_stats is thread-safe.
        We patch `refresh_from_db` with a mock object here because we don't want the
        underlying functionality to rely on `refresh_from_db` completing immediately
        before the update/save.
        """
        task_instance_a = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task_instance_b = ScanTask.objects.get(id=task_instance_a.id)

        assert 0 == task_instance_a.systems_count
        assert 0 == task_instance_b.systems_count

        with (
            patch.object(task_instance_a, "refresh_from_db"),
            patch.object(task_instance_b, "refresh_from_db"),
        ):
            task_instance_a.increment_stats("foo", increment_sys_count=True)
            task_instance_b.increment_stats("foo", increment_sys_count=True)

        task_instance_a.refresh_from_db()
        task_instance_b.refresh_from_db()

        assert 2 == task_instance_a.systems_count
        assert 2 == task_instance_b.systems_count

    def test_scantask_reset_stats(self, scan_job, source):
        """Test scan task reset stat feature."""
        task = ScanTask.objects.create(
            job=scan_job,
            source=source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.increment_stats(
            "foo",
            increment_sys_count=True,
            increment_sys_scanned=True,
            increment_sys_failed=True,
            increment_sys_unreachable=True,
        )
        assert 1 == task.systems_count
        assert 1 == task.systems_scanned
        assert 1 == task.systems_failed
        assert 1 == task.systems_unreachable
        task.reset_stats()
        assert 0 == task.systems_count
        assert 0 == task.systems_scanned
        assert 0 == task.systems_failed
        assert 0 == task.systems_unreachable


@pytest.mark.django_db
def test_cleanup_facts():
    """Test ScanTask.cleanup_facts method."""
    scan_task = ScanTaskFactory(scan_type=ScanTask.SCAN_TYPE_INSPECT)
    inspect_group = InspectGroupFactory()
    results = InspectResultFactory.create_batch(5, inspect_group=inspect_group)
    scan_task.inspect_groups.add(inspect_group)
    assert scan_task.get_result().count() == 5
    identity_key = "identity-key"
    # add a raw fact with identity key to "protect" one of the results
    protected_result_id = results[0].id
    RawFact.objects.create(
        name=identity_key, inspect_result_id=protected_result_id, value="some-value"
    )
    # other results won't be protected even with identity-key because value is not valid
    # or absent
    RawFact.objects.create(name=identity_key, inspect_result=results[1], value="")
    RawFact.objects.create(name=identity_key, inspect_result=results[2], value=None)
    RawFact.objects.create(name=identity_key, inspect_result=results[3], value={})
    scan_task.cleanup_facts(identity_key)
    assert scan_task.get_result().count() == 1
    assert InspectResult.objects.filter(id=protected_result_id).exists()
