"""Test the CeleryScanManager class."""

from unittest.mock import Mock, patch

import pytest

from api.models import ScanTask
from scanner import manager
from tests.factories import ScanJobFactory, ScanTaskFactory


class TestCeleryScanManager:
    """Test the CeleryScanManager class."""

    @patch("scanner.manager.set_scan_job_celery_task_id")
    def test_celery_manager_interface_put(self, set_celery_task_id_mock, faker, mocker):
        """Assert CeleryScanManager implements put."""
        set_celery_task_id_mock.return_value = None
        celery_manager = manager.CeleryScanManager()
        scan_job = Mock()
        scan_job_id = faker.pyint()
        scan_job.id = scan_job_id
        celery_task_id = faker.uuid4()
        scan_job_runner = Mock()
        scan_job_runner.run.return_value = celery_task_id
        scan_job_runner.scan_job.return_value = scan_job
        assert celery_manager.put(scan_job_runner) is None

    @patch("scanner.manager.get_scan_job_celery_task_id")
    def test_celery_manager_interface_kill_failed(self, get_celery_task_id_mock, faker):
        """Assert CeleryScanManager handles kill failures."""
        celery_manager = manager.CeleryScanManager()
        scan_job_id = faker.pyint()
        get_celery_task_id_mock.return_value = None
        scan_job = Mock()
        scan_job.id = scan_job_id
        scan_job.tasks = None
        assert celery_manager.kill(scan_job) is False

    def test_celery_manager_interface_kill_success(self, faker, mocker):
        """Assert CeleryScanManager handles kill successes."""
        mocker.patch.object(manager, "AsyncResult")
        mocker.patch.object(manager, "get_scan_job_celery_task_id")
        celery_manager = manager.CeleryScanManager()
        scan_job_id = faker.pyint()
        scan_job = Mock()
        scan_job.id = scan_job_id
        scan_job.tasks = None
        assert celery_manager.kill(scan_job) is True

    @pytest.mark.django_db
    def test_celery_manager_interface_kill_with_tasks_success(self, mocker):
        """Assert CeleryScanManager handles kill successes with valid Scan Tasks."""
        mocker.patch.object(manager, "AsyncResult")
        mocker.patch.object(manager, "get_scan_job_celery_task_id")
        celery_manager = manager.CeleryScanManager()
        scan_job = ScanJobFactory(status=ScanTask.RUNNING)
        ScanTaskFactory(job=scan_job)
        assert celery_manager.kill(scan_job) is True
