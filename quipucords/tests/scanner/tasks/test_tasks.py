"""Test the scanner.tasks module."""

import logging

import pytest
from django.test import override_settings

from api.scanjob.model import ScanJob
from api.scantask.model import ScanTask
from scanner import tasks
from tests.factories import ScanJobFactory, ScanTaskFactory


class UnexpectedError(Exception):
    """Dummy exception to raise in tests."""

    def __str__(self):
        """Get string representation."""
        return self.__class__.__name__


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_completed_if_all_tasks_are_completed():
    """Test finalize_scan sets expected COMPLETED status if all tasks are COMPLETED."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    tasks.finalize_scan.delay(scan_job_id=scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_completed_even_if_no_tasks_exist():
    """
    Test finalize_scan sets expected COMPLETED status if no tasks exist.

    This is exercising a possibly unexpected edge case with our existing scan job logic
    that we preserved when we wrote finalize_scan. If a task exists with not-COMPLETED
    status, the job fails. Otherwise, it succeeds even if the job has zero tasks.
    A scan with zero tasks reaching this part of the process *probably* never actually
    happens in practice, but since our code technically allows it, I'm defining this
    test so we know if/when this behavior changes.
    """
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    tasks.finalize_scan.delay(scan_job_id=scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_finalize_scan_failed_if_any_task_failed():
    """Test finalize_scan sets expected FAILED status if any task failed."""
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)
    ScanTaskFactory(status=ScanTask.FAILED, job=scan_job)
    ScanTaskFactory(status=ScanTask.COMPLETED, job=scan_job)
    tasks.finalize_scan.delay(scan_job_id=scan_job.id)
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED


@pytest.mark.django_db
def test_set_scan_task_failure_on_exception_happy_path(faker, caplog):
    """Test set_scan_task_failure_on_exception as a function decorator."""
    caplog.set_level(logging.WARNING)
    expected_return_value = faker.pyint()
    scan_task = ScanTaskFactory(status=ScanTask.PENDING)

    @tasks.set_scan_task_failure_on_exception
    def decorated_function(scan_task_id):
        assert scan_task_id == scan_task.id
        _scan_task = ScanTask.objects.get(id=scan_task_id)
        _scan_task.status = ScanTask.COMPLETED
        _scan_task.save()
        return expected_return_value

    assert decorated_function(scan_task_id=scan_task.id) == expected_return_value
    assert not caplog.messages
    scan_task.refresh_from_db()
    assert scan_task.status == ScanTask.COMPLETED


@pytest.mark.django_db
def test_set_scan_job_failure_on_exception_happy_path(faker, caplog):
    """Test set_scan_job_failure_on_exception as a function decorator."""
    caplog.set_level(logging.WARNING)
    expected_return_value = faker.pyint()
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)

    @tasks.set_scan_job_failure_on_exception
    def decorated_function(scan_job_id):
        assert scan_job_id == scan_job.id
        _scan_job = ScanJob.objects.get(id=scan_job_id)
        _scan_job.status = ScanTask.COMPLETED
        _scan_job.save()
        return expected_return_value

    assert decorated_function(scan_job_id=scan_job.id) == expected_return_value
    assert not caplog.messages
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.COMPLETED


@pytest.mark.django_db
def test_set_scan_task_failure_on_exception_missing_kwarg_warning(
    faker, mocker, caplog
):
    """Test set_scan_task_failure_on_exception warns on missing kwarg."""
    caplog.set_level(logging.WARNING)
    mock_inner_function = mocker.Mock()
    expected_return_value = faker.pyint()

    @tasks.set_scan_task_failure_on_exception
    def decorated_function():
        mock_inner_function()
        return expected_return_value

    assert decorated_function() == expected_return_value
    mock_inner_function.assert_called_once()
    assert (
        "Missing scan_task_id kwarg for decorated function decorated_function"
        in caplog.messages[0]
    )


@pytest.mark.django_db
def test_set_scan_job_failure_on_exception_missing_kwarg_warning(faker, mocker, caplog):
    """Test set_scan_job_failure_on_exception warns on missing kwarg."""
    caplog.set_level(logging.WARNING)
    mock_inner_function = mocker.Mock()
    expected_return_value = faker.pyint()

    @tasks.set_scan_job_failure_on_exception
    def decorated_function():
        mock_inner_function()
        return expected_return_value

    assert decorated_function() == expected_return_value
    mock_inner_function.assert_called_once()
    assert (
        "Missing scan_job_id kwarg for decorated function decorated_function"
        in caplog.messages[0]
    )


@pytest.mark.django_db
def test_set_scan_task_failure_on_exception_exception_sets_failed_status(caplog):
    """Test set_scan_task_failure_on_exception sets FAILED status."""
    caplog.set_level(logging.WARNING)
    scan_task = ScanTaskFactory(status=ScanTask.PENDING)

    @tasks.set_scan_task_failure_on_exception
    def decorated_function(scan_task_id):
        raise UnexpectedError

    decorated_function(scan_task_id=scan_task.id)
    assert (
        "Unexpected exception in decorated_function with "
        f"scan_task_id={scan_task.id}: UnexpectedError" in caplog.messages[0]
    )
    scan_task.refresh_from_db()
    assert scan_task.status == ScanTask.FAILED


@pytest.mark.django_db
def test_set_scan_job_failure_on_exception_very_unexpected_exception(faker, caplog):
    """Test set_scan_job_failure_on_exception unexpected exception logs errors."""
    caplog.set_level(logging.ERROR)
    bogus_scan_job_id = faker.pyint()

    @tasks.set_scan_job_failure_on_exception
    def decorated_function(scan_job_id):
        raise UnexpectedError

    decorated_function(scan_job_id=bogus_scan_job_id)
    assert (
        "Unexpected exception in decorated_function with "
        f"scan_job_id={bogus_scan_job_id}: UnexpectedError" in caplog.messages[0]
    )
    assert f"ScanJob({bogus_scan_job_id}).status_fail failed:" in caplog.messages[1]
    assert "ScanJob matching query does not exist" in caplog.messages[1]


@pytest.mark.django_db
def test_set_scan_task_failure_on_exception_very_unexpected_exception(faker, caplog):
    """Test set_scan_task_failure_on_exception unexpected exception logs errors."""
    caplog.set_level(logging.ERROR)
    bogus_scan_task_id = faker.pyint()

    @tasks.set_scan_task_failure_on_exception
    def decorated_function(scan_task_id):
        raise UnexpectedError

    decorated_function(scan_task_id=bogus_scan_task_id)
    assert (
        "Unexpected exception in decorated_function with "
        f"scan_task_id={bogus_scan_task_id}: UnexpectedError" in caplog.messages[0]
    )
    assert f"ScanTask({bogus_scan_task_id}).status_fail failed:" in caplog.messages[1]
    assert "ScanTask matching query does not exist" in caplog.messages[1]


@pytest.mark.django_db
def test_set_scan_job_failure_on_exception_exception_sets_failed_status(caplog):
    """Test set_scan_job_failure_on_exception sets FAILED status."""
    caplog.set_level(logging.WARNING)
    scan_job = ScanJobFactory(status=ScanTask.RUNNING)

    @tasks.set_scan_job_failure_on_exception
    def decorated_function(scan_job_id):
        raise UnexpectedError

    decorated_function(scan_job_id=scan_job.id)
    assert (
        "Unexpected exception in decorated_function with "
        f"scan_job_id={scan_job.id}" in caplog.messages[0]
    )
    scan_job.refresh_from_db()
    assert scan_job.status == ScanTask.FAILED
