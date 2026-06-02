"""Test the scanner.tasks celery task support function."""

from unittest.mock import Mock, patch

from django.conf import settings
from django.test import override_settings

from scanner.tasks import (
    celery_task_is_revoked,
    get_scan_job_celery_task_id,
    scan_job_celery_task_id_key,
    scan_job_is_canceled,
    set_scan_job_celery_task_id,
)


def test_celery_result_expires_is_long_enough():
    """CELERY_RESULT_EXPIRES must outlast any realistic scan duration."""
    value = getattr(settings, "CELERY_RESULT_EXPIRES", "MISSING")
    assert value != "MISSING", (
        "CELERY_RESULT_EXPIRES is not configured; "
        "Celery defaults to 24h which causes chord expiration for long scans."
    )
    min_ttl = 90 * 24 * 3600  # 90 days
    assert value >= min_ttl, (
        f"CELERY_RESULT_EXPIRES={value} is too short; "
        f"scans can run for weeks, need at least {min_ttl}s (90 days)."
    )


class TestCeleryTaskCache:
    """Test the celery tasks cache functions."""

    @patch("scanner.tasks.caches")
    def test_get_scan_job_celery_task(self, caches_mock, faker):
        """Test that getting a cache key accesses the redis cache."""
        scan_job_id = faker.pyint()
        key = scan_job_celery_task_id_key(scan_job_id)
        get_scan_job_celery_task_id(scan_job_id)
        caches_mock["redis"].get.assert_called_once_with(key)

    @patch("scanner.tasks.caches")
    def test_set_scan_job_celery_task_without_timeout(self, caches_mock, faker):
        """Test that setting a cache key uses the default ttl if not specified."""
        default_scan_job_ttl = faker.pyint(10, 60)
        with override_settings(QUIPUCORDS_SCAN_JOB_TTL=default_scan_job_ttl):
            celery_task_id = faker.uuid4()
            scan_job_id = faker.pyint()
            set_scan_job_celery_task_id(scan_job_id, celery_task_id)
            key = scan_job_celery_task_id_key(scan_job_id)
            caches_mock["redis"].set.assert_called_once_with(
                key, celery_task_id, default_scan_job_ttl
            )

    @patch("scanner.tasks.caches")
    def test_set_scan_job_celery_task_wit_timeout(self, caches_mock, faker):
        """Test that setting a cache key honors the TTL specified."""
        use_scan_job_ttl = faker.pyint(10, 60)
        celery_task_id = faker.uuid4()
        scan_job_id = faker.pyint()
        set_scan_job_celery_task_id(
            scan_job_id, celery_task_id, key_timeout=use_scan_job_ttl
        )
        key = scan_job_celery_task_id_key(scan_job_id)
        caches_mock["redis"].set.assert_called_once_with(
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
