"""Test the ScanTask model and serializer."""

import logging
from collections.abc import Callable
from functools import partial
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
    _scan = Scan.objects.create(name="scan_name", scan_type=ScanTask.SCAN_TYPE_INSPECT)
    _scan.sources.add(source)
    return _scan


@pytest.fixture
def scan_job(scan: Scan) -> ScanJob:
    """Create a ScanJob instance for tests."""
    return ScanJob.objects.create(scan=scan)


@pytest.mark.django_db
def test_successful_create(scan_job, source):
    """Create a scan task and serialize it."""
    task = ScanTask.objects.create(
        job=scan_job,
        source=source,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        status=ScanTask.PENDING,
    )
    serializer = ScanTaskSerializer(task)
    json_task = serializer.data
    expected = {
        "sequence_number": 0,
        "source": source.id,
        "scan_type": ScanTask.SCAN_TYPE_INSPECT,
        "status": "pending",
        "status_message": messages.ST_STATUS_MSG_PENDING,
        "systems_count": 0,
        "systems_scanned": 0,
        "systems_failed": 0,
        "systems_unreachable": 0,
    }
    assert expected == json_task


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_action,expected_status,expected_message,check_start_time,check_end_time",
    [
        [
            ScanTask.status_start,
            ScanTask.RUNNING,
            messages.ST_STATUS_MSG_RUNNING,
            True,
            False,
        ],
        [
            ScanTask.status_restart,
            ScanTask.PENDING,
            messages.ST_STATUS_MSG_RESTARTED,
            False,
            False,
        ],
        [
            ScanTask.status_pause,
            ScanTask.PAUSED,
            messages.ST_STATUS_MSG_PAUSED,
            False,
            False,
        ],
        [
            ScanTask.status_cancel,
            ScanTask.CANCELED,
            messages.ST_STATUS_MSG_CANCELED,
            False,
            True,
        ],
        [
            partial(ScanTask.status_complete, message="this was a triumph"),
            ScanTask.COMPLETED,
            "this was a triumph",
            False,
            True,
        ],
        [
            partial(ScanTask.status_fail, message="i'm making a note here"),
            ScanTask.FAILED,
            "i'm making a note here",
            False,
            True,
        ],
    ],
)
def test_scan_task_model_status_action(  # noqa: PLR0913
    model_action: Callable[[ScanTask], [None]],
    expected_status: str,
    expected_message: str,
    check_start_time: bool,
    check_end_time: bool,
    scan_job: ScanJob,
    source: Source,
):
    """Test status-related model actions on a new ScanTask instance."""
    task = ScanTask.objects.create(
        job=scan_job,
        source=source,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        status=ScanTask.PENDING,
    )
    model_action(task)
    assert expected_status == task.status
    assert expected_message == task.status_message
    if check_start_time:
        assert task.start_time is not None
    if check_end_time:
        assert task.end_time is not None


@pytest.mark.django_db
def test_scantask_increment(scan_job, source):
    """Test scan task increment feature."""
    task = ScanTask.objects.create(
        job=scan_job,
        source=source,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
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


@pytest.mark.django_db
def test_scantask_increment_stats_multiple_in_parallel(scan_job, source):
    """Test scan task increment two instances in parallel.

    This is a special case test to help ensure that increment_stats is thread-safe.
    We patch `refresh_from_db` with a mock object here because we don't want the
    underlying functionality to rely on `refresh_from_db` completing immediately
    before the update/save.
    """
    task_instance_a = ScanTask.objects.create(
        job=scan_job,
        source=source,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
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


@pytest.mark.django_db
def test_log_scan_message_normal(scan_job, source, caplog, faker):
    """Test _log_scan_message for a populated instance."""
    task = ScanTask.objects.create(job=scan_job, source=source)
    caplog.set_level(logging.INFO, logger="api.scantask.model")
    message = faker.sentence()
    task._log_scan_message(message)
    assert len(caplog.messages) == 1
    assert message in caplog.messages[0]


@pytest.mark.django_db
def test_log_scan_message_problematic(scan_job, caplog, faker):
    """Test _log_scan_message for an instance with no sources."""
    task = ScanTask.objects.create(job=scan_job)  # no sources!
    caplog.set_level(logging.INFO, logger="api.scantask.model")
    message = faker.sentence()
    task._log_scan_message(message)
    assert len(caplog.messages) == 2
    assert "Missing source" in caplog.messages[0]
    assert message in caplog.messages[1]


@pytest.mark.django_db
def test_scantask_model_str():
    """Test the __str__ method."""
    scan_task = ScanTaskFactory()
    scan_task_str = f"{scan_task}"
    assert f"id={scan_task.id}" in scan_task_str
    assert f"scan_type={scan_task.scan_type}" in scan_task_str
    assert f"status={scan_task.status}" in scan_task_str
