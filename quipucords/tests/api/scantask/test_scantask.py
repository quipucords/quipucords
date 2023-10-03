"""Test the API application."""

from datetime import datetime
from unittest.mock import patch

from django.core import management
from django.test import TestCase

from api import messages
from api.models import Credential, Scan, ScanJob, ScanTask, Source
from api.serializers import ScanTaskSerializer


def dummy_start():
    """Create a dummy method for testing."""


class ScanTaskTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        management.call_command("flush", "--no-input")
        self.cred = Credential.objects.create(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.source = Source.objects.create(
            name="source1", source_type="network", port=22
        )
        self.source.credentials.add(self.cred)

        # Create scan configuration
        scan = Scan.objects.create(
            name="scan_name", scan_type=ScanTask.SCAN_TYPE_CONNECT
        )

        # Add source to scan
        scan.sources.add(self.source)

        # Create Job
        self.scan_job = ScanJob.objects.create(scan=scan)

    def test_successful_create(self):
        """Create a scan task and serialize it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        serializer = ScanTaskSerializer(task)
        json_task = serializer.data
        self.assertEqual(
            {
                "sequence_number": 0,
                "source": 1,
                "scan_type": ScanTask.SCAN_TYPE_CONNECT,
                "status": "pending",
                "status_message": messages.ST_STATUS_MSG_PENDING,
                "systems_count": 0,
                "systems_scanned": 0,
                "systems_failed": 0,
                "systems_unreachable": 0,
            },
            json_task,
        )

    def test_successful_start(self):
        """Create a scan task and start it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        start_time = datetime.utcnow()
        task.status_start()
        self.assertEqual(messages.ST_STATUS_MSG_RUNNING, task.status_message)
        self.assertEqual(task.status, ScanTask.RUNNING)
        self.assertEqual(
            start_time.replace(microsecond=0), task.start_time.replace(microsecond=0)
        )

    def test_successful_restart(self):
        """Create a scan task and restart it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.status_restart()
        self.assertEqual(messages.ST_STATUS_MSG_RESTARTED, task.status_message)
        self.assertEqual(task.status, ScanTask.PENDING)

    def test_successful_pause(self):
        """Create a scan task and status_pause it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.status_pause()
        self.assertEqual(messages.ST_STATUS_MSG_PAUSED, task.status_message)
        self.assertEqual(task.status, ScanTask.PAUSED)

    def test_successful_cancel(self):
        """Create a scan task and cancel it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        end_time = datetime.utcnow()
        task.status_cancel()
        self.assertEqual(messages.ST_STATUS_MSG_CANCELED, task.status_message)
        self.assertEqual(task.status, ScanTask.CANCELED)
        self.assertEqual(
            end_time.replace(microsecond=0), task.end_time.replace(microsecond=0)
        )

    def test_successful_complete(self):
        """Create a scan task and complete it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        end_time = datetime.utcnow()
        task.status_complete("great")
        self.assertEqual("great", task.status_message)
        self.assertEqual(task.status, ScanTask.COMPLETED)
        self.assertEqual(
            end_time.replace(microsecond=0), task.end_time.replace(microsecond=0)
        )

    def test_scantask_fail(self):
        """Create a scan task and fail it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        msg = "Test Fail."
        end_time = datetime.utcnow()
        task.status_fail(msg)
        self.assertEqual(msg, task.status_message)
        self.assertEqual(task.status, ScanTask.FAILED)
        self.assertEqual(
            end_time.replace(microsecond=0), task.end_time.replace(microsecond=0)
        )

    def test_scantask_increment(self):
        """Test scan task increment feature."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
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
        self.assertEqual(1, task.systems_count)
        self.assertEqual(1, task.systems_scanned)
        self.assertEqual(1, task.systems_failed)
        self.assertEqual(1, task.systems_unreachable)
        task.increment_stats(
            "foo",
            increment_sys_count=True,
            increment_sys_scanned=True,
            increment_sys_failed=True,
            increment_sys_unreachable=True,
        )
        self.assertEqual(2, task.systems_count)
        self.assertEqual(2, task.systems_scanned)
        self.assertEqual(2, task.systems_failed)
        self.assertEqual(2, task.systems_unreachable)

    def test_scantask_increment_stats_multiple_in_parallel(self):
        """Test scan task increment two instances in parallel.

        This is a special case test to help ensure that increment_stats is thread-safe.
        We patch `refresh_from_db` with a mock object here because we don't want the
        underlying functionality to rely on `refresh_from_db` completing immediately
        before the update/save.
        """
        task_instance_a = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task_instance_b = ScanTask.objects.get(id=task_instance_a.id)

        self.assertEqual(0, task_instance_a.systems_count)
        self.assertEqual(0, task_instance_b.systems_count)

        with patch.object(task_instance_a, "refresh_from_db"), patch.object(
            task_instance_b, "refresh_from_db"
        ):
            task_instance_a.increment_stats("foo", increment_sys_count=True)
            task_instance_b.increment_stats("foo", increment_sys_count=True)

        task_instance_a.refresh_from_db()
        task_instance_b.refresh_from_db()

        self.assertEqual(2, task_instance_a.systems_count)
        self.assertEqual(2, task_instance_b.systems_count)

    def test_scantask_reset_stats(self):
        """Test scan task reset stat feature."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
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
        self.assertEqual(1, task.systems_count)
        self.assertEqual(1, task.systems_scanned)
        self.assertEqual(1, task.systems_failed)
        self.assertEqual(1, task.systems_unreachable)
        task.reset_stats()
        self.assertEqual(0, task.systems_count)
        self.assertEqual(0, task.systems_scanned)
        self.assertEqual(0, task.systems_failed)
        self.assertEqual(0, task.systems_unreachable)
