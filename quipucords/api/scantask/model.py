"""Defines the models used with the API application.

These models are used in the REST definitions.
"""

import logging
from datetime import datetime
from functools import cached_property

from django.db import models, transaction
from django.db.models import F
from django.utils.translation import gettext as _

from api import messages
from api.common.models import BaseModel
from api.connresult.model import TaskConnectionResult
from api.inspectresult.model import InspectResult, RawFact
from api.source.model import Source

logger = logging.getLogger(__name__)


class ScanTask(BaseModel):
    """The scan task captures a single source for a scan."""

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
    systems_count = models.PositiveIntegerField(default=0)
    systems_scanned = models.PositiveIntegerField(default=0)
    systems_failed = models.PositiveIntegerField(default=0)
    systems_unreachable = models.PositiveIntegerField(default=0)
    sequence_number = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    # Connect/Inspect task fields
    source = models.ForeignKey(Source, null=True, on_delete=models.SET_NULL)

    # Connect task field
    connection_result = models.OneToOneField(
        TaskConnectionResult, null=True, on_delete=models.SET_NULL
    )

    @cached_property
    def scan_job_task_count(self):
        """
        Get the number of tasks.

        This retains a cached copy of the task count during the runtime of an instance
        and avoids unnecessary lookups since we may frequently log this value.
        """
        return self.job.tasks.all().count()

    def reset_scan_job_task_count(self):
        """Reset the cached `scan_job_task_count` counter."""
        if hasattr(self, "scan_job_task_count"):
            del self.scan_job_task_count

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
        message = (
            f"{prefix} Stats:"
            f" systems_count={self.systems_count},"
            f" systems_scanned={self.systems_scanned},"
            f" systems_failed={self.systems_failed},"
            f" systems_unreachable={self.systems_unreachable}"
        )
        self.log_message(message)

    def _log_fingerprint_stats(self, prefix):
        """Log stats for fingerprinter."""
        system_fingerprint_count = 0
        if self.job.report:
            self.job.report.refresh_from_db()

            if self.job.report.deployment_report:
                system_fingerprint_count = (
                    self.job.report.deployment_report.system_fingerprints.count()
                )
        message = f"{prefix} Stats: system_fingerprint_count={system_fingerprint_count}"
        self.log_message(message)

    # All task types
    def log_message(
        self, message, log_level=logging.INFO, static_options=None, exception=None
    ):
        """Log a message for this task."""
        if exception:
            logger.exception("Got an exception.")

        if self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            self._log_fingerprint_message(message, log_level)
        else:
            self._log_scan_message(message, log_level, static_options)

    # All scan task types
    def _log_scan_message(self, message, log_level=logging.INFO, static_options=None):
        """Log a message for this task."""
        if not self.source:
            logger.warning("Missing source for job ID %s", self.job_id)
            source_type = None
            source_name = None
        else:
            source_type = self.source.source_type
            source_name = self.source.name
        if static_options is not None:
            actual_message = (
                f"Job {self.job_id:d},"
                f" Task {self.sequence_number:d} of {self.scan_job_task_count:d}"
                f" ({self.scan_type}, {source_type}, {source_name}) - "
            )
        else:
            elapsed_time = self._compute_elapsed_time()
            actual_message = (
                f"Job {self.job_id:d},"
                f" Task {self.sequence_number:d} of {self.scan_job_task_count:d}"
                f" ({self.scan_type}, {source_type}, {source_name},"
                f" elapsed_time: {elapsed_time:.0f}s) - "
            )
        actual_message += message.strip()
        logger.log(log_level, actual_message)

    # Fingerprint task type
    def _log_fingerprint_message(self, message, log_level=logging.INFO):
        """Log a message for this task."""
        elapsed_time = self._compute_elapsed_time()
        details_report_id = None
        if self.job.report:
            details_report_id = self.job.report.id
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
    def update_stats(  # noqa: PLR0913
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
        self.refresh_from_db()
        self.systems_count = 0
        self.systems_scanned = 0
        self.systems_failed = 0
        self.systems_unreachable = 0

        self.save()
        self._log_stats("INITIALIZING SYSTEM COUNTS - default all to 0")

    # All task types
    @transaction.atomic
    def increment_stats(  # noqa: PLR0913
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
        update_kwargs = {}
        if increment_sys_count:
            update_kwargs["systems_count"] = F("systems_count") + 1
        if increment_sys_scanned:
            update_kwargs["systems_scanned"] = F("systems_scanned") + 1
        if increment_sys_failed:
            update_kwargs["systems_failed"] = F("systems_failed") + 1
        if increment_sys_unreachable:
            update_kwargs["systems_unreachable"] = F("systems_unreachable") + 1

        if update_kwargs:
            ScanTask.objects.filter(id=self.id).update(**update_kwargs)
            self.refresh_from_db()
            description = f"{prefix} {name}."
            self._log_stats(description)

    # All task types
    def status_start(self):
        """Change status to RUNNING."""
        self.start_time = datetime.utcnow()
        self.status = ScanTask.RUNNING
        self.status_message = _(messages.ST_STATUS_MSG_RUNNING)
        self.save()
        self.reset_scan_job_task_count()
        self.log_current_status()

    # All task types
    def status_restart(self):
        """Change status to PENDING."""
        self.status = ScanTask.PENDING
        self.status_message = _(messages.ST_STATUS_MSG_RESTARTED)
        self.save()
        self.log_current_status()

    # All task types
    def status_pause(self):
        """Change status to PAUSED."""
        self.status = ScanTask.PAUSED
        self.status_message = _(messages.ST_STATUS_MSG_PAUSED)
        self.save()
        self.log_current_status()

    # All task types
    def status_cancel(self):
        """Change status to CANCELED."""
        self.end_time = datetime.utcnow()
        self.status = ScanTask.CANCELED
        self.status_message = _(messages.ST_STATUS_MSG_CANCELED)
        self.save()
        self.log_current_status()

    # All task types
    @transaction.atomic
    def status_complete(self, message=None):
        """Change status to COMPLETED."""
        self.refresh_from_db()
        self.end_time = datetime.utcnow()
        self.status = ScanTask.COMPLETED
        if message:
            self.status_message = message
            self.log_message(self.status_message)
        else:
            self.status_message = _(messages.ST_STATUS_MSG_COMPLETED)

        self.save()
        self._log_stats("COMPLETION STATS.")
        self.log_current_status()

    # All task types
    def status_fail(self, message):
        """Change status to FAILED.

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
        fact_list = []

        for inspect_result in (
            InspectResult.objects.filter(inspect_group__in=self.inspect_groups.all())
            .prefetch_related("facts")
            .all()
        ):
            fact_dict = {
                raw_fact.name: raw_fact.value for raw_fact in inspect_result.facts.all()
            }
            fact_list.append(fact_dict)
        return fact_list

    # inspect task
    @transaction.atomic
    def cleanup_facts(self, identity_key):
        """Cleanup inspection facts.

        :param identity_key: A key that identifies the system.  If
        key not present, the system is discarded.
        """
        if self.scan_type != ScanTask.SCAN_TYPE_INSPECT:
            return
        # TODO: should we even be doing this cleanup without logging?
        # my gut feeling is just mark it as failed (and stop post processing
        # failed data)
        valid_identity_raw_facts = (
            RawFact.objects.filter(
                inspect_result__inspect_group__in=self.inspect_groups.all(),
                name=identity_key,
            )
            .exclude(value__isnull=True)
            .exclude(value="")
            .exclude(value={})
        )
        invalid_results = InspectResult.objects.filter(
            inspect_group__in=self.inspect_groups.all()
        ).exclude(facts__in=valid_identity_raw_facts)
        if not invalid_results.exists():
            return
        logger.warning(
            "[task=%s] %d invalid results found. Deleting...",
            self.id,
            invalid_results.count(),
        )
        invalid_results.delete()

    def get_result(self):
        """Access results from ScanTask.

        Results are expected to be persisted. This method should
        understand how to read persisted results into a dictionary
        using a ScanTask object so others can retrieve them if needed.

        :returns: Scan result object for task (either TaskConnectionResult,
            TaskInspectionResult, or Report)
        """
        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            return InspectResult.objects.filter(
                inspect_group__in=self.inspect_groups.all()
            ).all()
        elif self.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            return self.connection_result
        elif self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            return self.job.report
        return None

    def log_raw_facts(self, log_level=logging.INFO):
        """Log stored raw facts."""
        raw_facts = self.get_facts()
        if not raw_facts:
            self.log_message(
                "Impossible to log absent raw facts.",
                log_level=max(logging.ERROR, log_level),
            )
            return
        # Using a pure logger to avoid the extra context information added
        # by log_message method.
        logger.log(log_level, f"{'raw facts':-^50}")
        logger.log(log_level, raw_facts)
        logger.log(log_level, "-" * 50)
