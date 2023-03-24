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
        scan = Scan(name="scan_name", scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan.save()

        # Add source to scan
        scan.sources.add(self.source)

        # Create Job
        self.scan_job = ScanJob(scan=scan)
        self.scan_job.save()

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
        assert {
            "sequence_number": 0,
            "source": 1,
            "scan_type": ScanTask.SCAN_TYPE_CONNECT,
            "status": "pending",
            "status_message": messages.ST_STATUS_MSG_PENDING,
        } == json_task

    def test_successful_start(self):
        """Create a scan task and start it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        start_time = datetime.utcnow()
        task.start()
        task.save()
        assert messages.ST_STATUS_MSG_RUNNING == task.status_message
        assert task.status == ScanTask.RUNNING
        assert start_time.replace(microsecond=0) == task.start_time.replace(
            microsecond=0
        )

    def test_successful_restart(self):
        """Create a scan task and restart it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.restart()
        task.save()
        assert messages.ST_STATUS_MSG_RESTARTED == task.status_message
        assert task.status == ScanTask.PENDING

    def test_successful_pause(self):
        """Create a scan task and pause it."""
        task = ScanTask.objects.create(
            job=self.scan_job,
            source=self.source,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
        )
        task.pause()
        task.save()
        assert messages.ST_STATUS_MSG_PAUSED == task.status_message
        assert task.status == ScanTask.PAUSED

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
        assert messages.ST_STATUS_MSG_CANCELED == task.status_message
        assert task.status == ScanTask.CANCELED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

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
        assert "great" == task.status_message
        assert task.status == ScanTask.COMPLETED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

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
        assert MSG == task.status_message
        assert task.status == ScanTask.FAILED
        assert end_time.replace(microsecond=0) == task.end_time.replace(microsecond=0)

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
        assert 1 == task.systems_count
        assert 1 == task.systems_scanned
        assert 1 == task.systems_failed
        assert 1 == task.systems_unreachable
        task.reset_stats()
        assert None is task.systems_count
        assert None is task.systems_scanned
        assert None is task.systems_failed
        assert None is task.systems_unreachable

        (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
        ) = task.calculate_counts()

        assert systems_count == 0
        assert systems_scanned == 0
        assert systems_failed == 0
        assert systems_unreachable == 0

    def test_calculate_counts(self):
        """Test calculate counts."""
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
        (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
        ) = task.calculate_counts()
        assert systems_count == 1
        assert systems_scanned == 1
        assert systems_failed == 1
        assert systems_unreachable == 1
