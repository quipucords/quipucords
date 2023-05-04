"""Defines the models used with the API application.

These models are used in the REST definitions.
"""
import logging
from datetime import datetime

from django.db import models, transaction
from django.utils.translation import gettext as _

from api import messages
from api.connresult.model import TaskConnectionResult
from api.details_report.model import DetailsReport
from api.inspectresult.model import TaskInspectionResult
from api.scantask.queryset import ScanTaskQuerySet
from api.source.model import Source

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanTask(models.Model):
    """The scan task captures a single source for a scan."""

    # pylint: disable=too-many-instance-attributes
    SCAN_TYPE_CONNECT = "connect"
    SCAN_TYPE_INSPECT = "inspect"
    SCAN_TYPE_FINGERPRINT = "fingerprint"
    SCANTASK_TYPE_CHOICES = (
        (SCAN_TYPE_CONNECT, SCAN_TYPE_CONNECT),
        (SCAN_TYPE_INSPECT, SCAN_TYPE_INSPECT),
        (SCAN_TYPE_FINGERPRINT, SCAN_TYPE_FINGERPRINT),
    )

    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELED = "canceled"
    COMPLETED = "completed"
    FAILED = "failed"
    STATUS_CHOICES = (
        (CREATED, CREATED),
        (PENDING, PENDING),
        (RUNNING, RUNNING),
        (PAUSED, PAUSED),
        (COMPLETED, COMPLETED),
        (CANCELED, CANCELED),
        (FAILED, FAILED),
    )

    # All task fields
    scan_type = models.CharField(max_length=12, choices=SCANTASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    status_message = models.TextField(
        null=True, default=_(messages.ST_STATUS_MSG_PENDING)
    )
    prerequisites = models.ManyToManyField("ScanTask")
    job = models.ForeignKey("api.ScanJob", models.CASCADE, related_name="tasks")
    systems_count = models.PositiveIntegerField(null=True)
    systems_scanned = models.PositiveIntegerField(null=True)
    systems_failed = models.PositiveIntegerField(null=True)
    systems_unreachable = models.PositiveIntegerField(null=True)
    sequence_number = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    # Connect/Inspect task fields
    source = models.ForeignKey(Source, null=True, on_delete=models.CASCADE)

    # Connect task field
    connection_result = models.OneToOneField(
        TaskConnectionResult, null=True, on_delete=models.CASCADE
    )

    # Inspect task field
    inspection_result = models.OneToOneField(
        TaskInspectionResult, null=True, on_delete=models.CASCADE
    )

    # Fingerprint task field
    details_report = models.ForeignKey(
        DetailsReport, null=True, on_delete=models.CASCADE
    )

    # custom queryset / object manager
    objects = ScanTaskQuerySet.as_manager()

    def __init__(self, *args, **kwargs):
        """Initialize a ScanTask."""
        super().__init__(*args, **kwargs)
        self.scan_job_task_count = None

    def __str__(self):
        """Convert to string."""
        return (
            "{"
            f"id:{self.id},"
            f" job:{self.job_id},"
            f" scan_type:{self.scan_type},"
            f" status:{self.status},"
            f" source:{self.source_id},"
            f" sequence_number:{self.sequence_number},"
            f" systems_count: {self.systems_count},"
            f" systems_scanned: {self.systems_scanned},"
            f" systems_failed: {self.systems_failed},"
            f" systems_unreachable: {self.systems_unreachable},"
            f" start_time: {self.start_time}"
            f" end_time: {self.end_time},"
            f" connection_result: {self.connection_result_id},"
            f" inspection_result: {self.inspection_result_id},"
            f" details_report: {self.details_report_id}"
            "}"
        )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_TASKS_MSG)
        ordering = ("sequence_number",)
        unique_together = ["job", "scan_type", "source"]

    # all task types
    def log_current_status(self, show_status_message=False, log_level=logging.INFO):
        """Log current status of task."""
        if show_status_message:
            message = (
                f"STATE UPDATE ({self.status})."
                f" Additional status information: {self.status_message}"
            )
        else:
            message = f"STATE UPDATE ({self.status})"
        self.log_message(message, log_level=log_level)

    # fingerprint task type
    def _log_stats(self, prefix):
        """Log stats for scan."""
        if self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            self._log_fingerprint_stats(prefix)
        else:
            self._log_scan_stats(prefix)

    # connect/inspect task types
    def _log_scan_stats(self, prefix):
        """Log stats for scan."""
        sys_count = self.systems_count
        sys_failed = self.systems_failed
        sys_unreachable = self.systems_unreachable
        sys_scanned = self.systems_scanned
        if sys_count is None:
            sys_count = 0
        if sys_scanned is None:
            sys_scanned = 0
        if sys_failed is None:
            sys_failed = 0
        if sys_unreachable is None:
            sys_unreachable = 0
        message = (
            f"{prefix} Stats:"
            f" systems_count={sys_count},"
            f" systems_scanned={sys_scanned},"
            f" systems_failed={sys_failed},"
            f" systems_unreachable={sys_unreachable}"
        )
        self.log_message(message)

    def _log_fingerprint_stats(self, prefix):
        """Log stats for fingerprinter."""
        system_fingerprint_count = 0
        if self.details_report:
            self.details_report.refresh_from_db()
            # pylint: disable=using-constant-test
            if self.details_report.deployment_report:
                # pylint: disable=no-member
                system_fingerprint_count = (
                    self.details_report.deployment_report.system_fingerprints.count()
                )
        message = f"{prefix} Stats: system_fingerprint_count={system_fingerprint_count}"
        self.log_message(message)

    # All task types
    def log_message(
        self, message, log_level=logging.INFO, static_options=None, exception=None
    ):
        """Log a message for this task."""
        # pylint: disable=no-member
        if exception:
            logger.exception("Got an exception.")

        if self.scan_job_task_count is None:
            self.scan_job_task_count = self.job.tasks.all().count()
        if self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            self._log_fingerprint_message(message, log_level)
        else:
            self._log_scan_message(message, log_level, static_options)

    # All scan task types
    def _log_scan_message(self, message, log_level=logging.INFO, static_options=None):
        """Log a message for this task."""
        # pylint: disable=no-member
        if static_options is not None:
            actual_message = (
                f"Job {self.job_id:d},"
                f" Task {self.sequence_number:d} of {self.scan_job_task_count:d}"
                f" ({self.scan_type}, {self.source.source_type}, {self.source.name}) - "
            )
        else:
            elapsed_time = self._compute_elapsed_time()
            actual_message = (
                f"Job {self.job_id:d},"
                f" Task {self.sequence_number:d} of {self.scan_job_task_count:d}"
                f" ({self.scan_type}, {self.source.source_type}, {self.source.name},"
                f" elapsed_time: {elapsed_time:.0f}s) - "
            )
        actual_message += message.strip()
        logger.log(log_level, actual_message)

    # Fingerprint task type
    def _log_fingerprint_message(self, message, log_level=logging.INFO):
        """Log a message for this task."""
        elapsed_time = self._compute_elapsed_time()
        # pylint: disable=no-member
        details_report_id = None
        if self.details_report:
            details_report_id = self.details_report.id
        actual_message = (
            f"Job {self.job.id:d},"
            f" Task {self.sequence_number:d} of {self.scan_job_task_count:d}"
            f" ({self.scan_type}, details_report={details_report_id},"
            f" elapsed_time: {elapsed_time:.0f}s) - "
        )
        actual_message += message.strip()
        logger.log(log_level, actual_message)

    def _compute_elapsed_time(self):
        """Compute elapsed time."""
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (datetime.utcnow() - self.start_time).total_seconds()
        return elapsed_time

    # All task types
    @transaction.atomic
    def update_stats(
        self,
        description,
        sys_count=None,
        sys_scanned=None,
        sys_failed=None,
        sys_unreachable=None,
    ):
        """Update scan task stats.

        :param description: Description to be logged with stats.
        :param sys_count: Total number of systems.
        :param sys_scanned: Systems scanned.
        :param sys_failed: Systems failed during scan.
        :param sys_unreachable: Systems unreachable during scan.
        """
        # pylint: disable=too-many-arguments
        self.refresh_from_db()
        stats_changed = False
        if sys_count is not None and sys_count != self.systems_count:
            self.systems_count = sys_count
            stats_changed = True
        if sys_scanned is not None and sys_scanned != self.systems_scanned:
            self.systems_scanned = sys_scanned
            stats_changed = True
        if sys_failed is not None and sys_failed != self.systems_failed:
            self.systems_failed = sys_failed
            stats_changed = True
        if sys_unreachable is not None and sys_unreachable != self.systems_unreachable:
            self.systems_unreachable = sys_unreachable
            stats_changed = True

        if stats_changed:
            self.save()
        self._log_stats(description)

    # All task types
    @transaction.atomic
    def reset_stats(self):
        """Reset scan task stats default state."""
        # pylint: disable=too-many-arguments
        self.refresh_from_db()
        self.systems_count = None
        self.systems_scanned = None
        self.systems_failed = None
        self.systems_unreachable = None

        self.save()
        self._log_stats("INITIALIZING SYSTEM COUNTS - default all to 0")

    # All task types
    @transaction.atomic
    def increment_stats(
        self,
        name,
        increment_sys_count=False,
        increment_sys_scanned=False,
        increment_sys_failed=False,
        increment_sys_unreachable=False,
        prefix="PROCESSING",
    ):
        """Increment scan task stats.

        Helper method to increment and save values.  Log will be
        produced after stats are updated.
        :param description: Name of entity (host, ip, etc)
        :param increment_sys_count: True if should be incremented.
        :param increment_sys_scanned: True if should be incremented.
        :param increment_sys_failed: True if should be incremented.
        :param increment_sys_unreachable: True if should be incremented.
        """
        # pylint: disable=too-many-arguments
        self.refresh_from_db()
        sys_count = None
        sys_failed = None
        sys_unreachable = None
        sys_scanned = None
        if increment_sys_count:
            if self.systems_count is None:
                sys_count = 0
            else:
                sys_count = self.systems_count
            sys_count += 1
        if increment_sys_scanned:
            if self.systems_scanned is None:
                sys_scanned = 0
            else:
                sys_scanned = self.systems_scanned
            sys_scanned += 1
        if increment_sys_failed:
            if self.systems_failed is None:
                sys_failed = 0
            else:
                sys_failed = self.systems_failed
            sys_failed += 1
        if increment_sys_unreachable:
            if self.systems_unreachable is None:
                sys_unreachable = 0
            else:
                sys_unreachable = self.systems_unreachable
            sys_unreachable += 1
        stat_string = f"{prefix} {name}."
        self.update_stats(
            stat_string,
            sys_count=sys_count,
            sys_scanned=sys_scanned,
            sys_failed=sys_failed,
            sys_unreachable=sys_unreachable,
        )

    # All task types
    def calculate_counts(self):
        """Calculate scan counts for task.

        :return: systems_count, systems_scanned,
        systems_failed, systems_unreachable
        """
        systems_count = 0
        systems_scanned = 0
        systems_failed = 0
        systems_unreachable = 0
        if self.systems_count is not None:
            if systems_count is None:
                systems_count = 0
            systems_count += self.systems_count
        if self.systems_scanned is not None:
            if systems_scanned is None:
                systems_scanned = 0
            systems_scanned += self.systems_scanned
        if self.systems_failed is not None:
            if systems_failed is None:
                systems_failed = 0
            systems_failed += self.systems_failed
        if self.systems_unreachable is not None:
            if systems_unreachable is None:
                systems_unreachable = 0
            systems_unreachable += self.systems_unreachable

        return systems_count, systems_scanned, systems_failed, systems_unreachable

    # All task types
    def start(self):
        """Change status to RUNNING."""
        self.start_time = datetime.utcnow()
        self.status = ScanTask.RUNNING
        self.status_message = _(messages.ST_STATUS_MSG_RUNNING)
        self.save()
        # pylint: disable=no-member
        self.scan_job_task_count = self.job.tasks.all().count()
        self.log_current_status()

    # All task types
    def restart(self):
        """Change status to PENDING."""
        self.status = ScanTask.PENDING
        self.status_message = _(messages.ST_STATUS_MSG_RESTARTED)
        self.save()
        self.log_current_status()

    # All task types
    def pause(self):
        """Change status to PAUSED."""
        self.status = ScanTask.PAUSED
        self.status_message = _(messages.ST_STATUS_MSG_PAUSED)
        self.save()
        self.log_current_status()

    # All task types
    def cancel(self):
        """Change status to CANCELED."""
        self.end_time = datetime.utcnow()
        self.status = ScanTask.CANCELED
        self.status_message = _(messages.ST_STATUS_MSG_CANCELED)
        self.save()
        self.log_current_status()

    # All task types
    @transaction.atomic
    def complete(self, message=None):
        """Complete a task."""
        self.refresh_from_db()
        self.end_time = datetime.utcnow()
        self.status = ScanTask.COMPLETED
        if message:
            self.status_message = message
            self.log_message(self.status_message)
        else:
            self.status_message = _(messages.ST_STATUS_MSG_COMPLETED)

        if self.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
            if self.systems_count is None:
                self.systems_count = 0
            if self.systems_scanned is None:
                self.systems_scanned = 0
            if self.systems_failed is None:
                self.systems_failed = 0
        self.save()
        self._log_stats("COMPLETION STATS.")
        self.log_current_status()

    # All task types
    def fail(self, message):
        """Fail a task.

        :param message: The error message associated with failure
        """
        self.end_time = datetime.utcnow()
        self.status = ScanTask.FAILED
        self.status_message = message
        self.log_message(self.status_message, log_level=logging.ERROR)
        self.save()
        self._log_stats("FAILURE STATS.")
        self.log_current_status(show_status_message=True, log_level=logging.ERROR)

    def get_facts(self):
        """Access inspection facts."""
        if self.scan_type != ScanTask.SCAN_TYPE_INSPECT:
            return []
        raw_facts_queryset = self.__class__.objects.filter(id=self.id).raw_facts()
        return list(raw_facts_queryset.raw_facts_per_system().values())

    # inspect task
    @transaction.atomic
    def cleanup_facts(self, identity_key):
        """Cleanup inspection facts.

        :param identity_key: A key that identifies the system.  If
        key not present, the system is discarded.
        """
        # pylint: disable=too-many-nested-blocks
        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            system_results = self.get_result()
            if system_results:
                # Process all results that were save to db
                for system_result in system_results.systems.all():
                    fact = {}
                    for raw_fact in system_result.facts.all():
                        if not raw_fact.value or raw_fact.value == "":
                            continue
                        # Load values as JSON
                        fact[raw_fact.name] = raw_fact.value

                    if fact.get(identity_key) is None:
                        system_result.facts.all().delete()
                        system_result.delete()

    # all tasks
    # pylint: disable=no-else-return
    def get_result(self):
        """Access results from ScanTask.

        Results are expected to be persisted. This method should
        understand how to read persisted results into a dictionary
        using a ScanTask object so others can retrieve them if needed.

        :returns: Scan result object for task (either TaskConnectionResult,
            TaskInspectionResult, or DetailsReport)
        """
        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            return self.inspection_result
        elif self.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            return self.connection_result
        elif self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            return self.details_report
        return None
