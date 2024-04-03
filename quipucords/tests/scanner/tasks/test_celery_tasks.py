"""Test the scanner.tasks celery task support function."""

from unittest.mock import Mock, patch

from django.test import override_settings

from scanner.tasks import (
    celery_task_is_revoked,
    get_scan_job_celery_task_id,
    scan_job_celery_task_id_key,
    scan_job_is_canceled,
    set_scan_job_celery_task_id,
)


class TestCeleryTaskCache:
    """Test the celery tasks cache functions."""

    @patch("scanner.tasks.redis_cache")
    def test_get_scan_job_celery_task(self, redis_cache_mock, faker):
        """Test that getting a cache key accesses the redis cache."""
        scan_job_id = faker.pyint()
        key = scan_job_celery_task_id_key(scan_job_id)
        get_scan_job_celery_task_id(scan_job_id)
        assert redis_cache_mock.get.called_once_with(key)

    @patch("scanner.tasks.redis_cache")
    def test_set_scan_job_celery_task_without_timeout(self, redis_cache_mock, faker):
        """Test that setting a cache key uses the default ttl if not specified."""
        default_scan_job_ttl = faker.pyint(10, 60)
        with override_settings(QPC_SCAN_JOB_TTL=default_scan_job_ttl):
            celery_task_id = faker.uuid4()
            scan_job_id = faker.pyint()
            set_scan_job_celery_task_id(scan_job_id, celery_task_id)
            key = scan_job_celery_task_id_key(celery_task_id)
            assert redis_cache_mock.set.called_once_with(
                key, celery_task_id, default_scan_job_ttl
            )

    @patch("scanner.tasks.redis_cache")
    def test_set_scan_job_celery_task_wit_timeout(self, redis_cache_mock, faker):
        """Test that setting a cache key honors the TTL specified."""
        use_scan_job_ttl = faker.pyint(10, 60)
        celery_task_id = faker.uuid4()
        scan_job_id = faker.pyint()
        set_scan_job_celery_task_id(
            scan_job_id, celery_task_id, key_timeout=use_scan_job_ttl
        )
        key = scan_job_celery_task_id_key(celery_task_id)
        assert redis_cache_mock.set.called_once_with(
            key, celery_task_id, use_scan_job_ttl
        )


class TestCeleryTaskRevoked:
    """Test the celery tasks revoked function."""

    @patch("scanner.tasks.celery_inspect")
    def test_celery_task_is_revoked(self, celery_inspect_mock, faker):
        """Test that celery task is revoked returns True."""
        worker_hostname = faker.hostname()
        celery_task_id = faker.uuid4()
        celery_task = Mock()
        celery_task.request.hostname = worker_hostname
        celery_inspect_mock.revoked.return_value = {
            str(worker_hostname): [celery_task_id]
        }
        assert celery_task_is_revoked(celery_task, celery_task_id) is True

    @patch("scanner.tasks.celery_inspect")
    def test_celery_task_is_not_revoked(self, celery_inspect_mock, faker):
        """Test that celery task is revoked returns False."""
        worker_hostname = faker.hostname()
        celery_task_id = faker.uuid4()
        celery_task = Mock()
        celery_task.request.hostname = worker_hostname
        celery_inspect_mock.revoked.return_value = {
            str(worker_hostname): [faker.uuid4(), faker.uuid4()]
        }
        assert celery_task_is_revoked(celery_task, celery_task_id) is False

    @patch("scanner.tasks.celery_task_is_revoked", return_value=True)
    def test_scan_job_is_canceled(self, faker):
        """Test that scan job is canceled calls celery_task_is_revoked."""
        scan_job_id = faker.pyint()
        celery_task_id = faker.uuid4()
        with patch(
            "scanner.tasks.get_scan_job_celery_task_id", return_value=celery_task_id
        ):
            assert scan_job_is_canceled(Mock(), scan_job_id) is True
