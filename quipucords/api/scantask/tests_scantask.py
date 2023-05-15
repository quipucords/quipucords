"""Test the API application."""

from datetime import datetime

from django.core import management
from django.test import TestCase

from api import messages
from api.models import Credential, Scan, ScanJob, ScanTask, Source
from api.serializers import ScanTaskSerializer


def dummy_start():
    """Create a dummy method for testing."""


# pylint: disable=unused-argument
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
        self.cred_for_upload = self.cred.id

        self.source = Source(name="source1", source_type="network", port=22)
        self.source.save()
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
        task.save()
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
        task.save()
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
        task.save()
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
        task.cancel()
        task.save()
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
        task.complete("great")
        task.save()
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
        # pylint: disable=invalid-name
        MSG = "Test Fail."
        end_time = datetime.utcnow()
        task.fail(MSG)
        task.save()
        self.assertEqual(MSG, task.status_message)
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
        # pylint: disable=invalid-name
        task.save()
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

    def test_scantask_reset_stats(self):
        """Test scan task reset stat feature."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        # pylint: disable=invalid-name
        task.save()
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
