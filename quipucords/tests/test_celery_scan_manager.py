"""Test the CeleryScanManager class."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from scanner import manager


@pytest.fixture(scope="module")
def scan_manager():
    """
    Override conftest.scan_manager pytest fixture to do nothing in this test module.

    This is necessary because conftest.scan_manager is set to autouse=True, which means
    it patches *all* tests, but we specifically *do not want* its patches applied here.
    """


# @pytest.mark.django_db
class TestCeleryScanManager:
    """Test the CeleryScanManager class."""

    def test_default_scan_manager_setting(self):
        """Assert the default manager class has not changed."""
        with override_settings(QPC_ENABLE_CELERY_SCAN_MANAGER=False):
            manager.reinitialize()
            assert isinstance(manager.SCAN_MANAGER, manager.Manager)
            assert manager.SCAN_MANAGER.__class__.__name__ == "Manager"

    def test_celery_scan_manager_setting(self):
        """Assert the manager class changes to Celery."""
        with override_settings(QPC_ENABLE_CELERY_SCAN_MANAGER=True):
            manager.reinitialize()
            assert manager.SCAN_MANAGER.__class__.__name__ == "CeleryScanManager"

    def test_celery_manager_interface_isalive(self):
        """Assert CeleryScanManager implements Manager isalive."""
        celery_manager = manager.CeleryScanManager()
        assert celery_manager.is_alive()

    def test_celery_manager_interface_start(self):
        """Assert CeleryScanManager implements Manager start."""
        celery_manager = manager.CeleryScanManager()
        assert celery_manager.start() is True

    @patch("scanner.manager.isinstance", return_value=True)
    def test_celery_manager_interface_put(self, faker):
        """Assert CeleryScanManager implements put."""
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
        scan_job.tasks = {}
        assert celery_manager.kill(scan_job, "cancel") is False

    @patch("celery.result.AsyncResult")
    @patch("scanner.manager.get_scan_job_celery_task_id")
    def test_celery_manager_interface_kill_success(
        self, async_result_mock, get_celery_task_id_mock, faker
    ):
        """Assert CeleryScanManager handles kill successes."""
        celery_manager = manager.CeleryScanManager()
        scan_job_id = faker.pyint()
        celery_task_id = faker.uuid4()
        get_celery_task_id_mock.return_value = celery_task_id
        scan_job = Mock()
        scan_job.id = scan_job_id
        scan_job.tasks = {}
        celery_task = Mock()
        async_result_mock.return_value = celery_task
        celery_task.revoke.return_value = None
        assert celery_manager.kill(scan_job, "cancel") is True
