"""Defines the models used with the API application.

These models are used in the REST definitions.
"""

import logging
from datetime import UTC, datetime

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils.translation import gettext as _

from api import messages
from api.common.models import BaseModel
from api.connresult.model import JobConnectionResult, TaskConnectionResult
from api.inspectresult.model import InspectGroup, InspectResult, RawFact
from api.report.model import Report
from api.scan.model import Scan
from api.scanjob.queryset import ScanJobQuerySet
from api.scantask.model import ScanTask
from api.source.model import Source

logger = logging.getLogger(__name__)


class ScanJob(BaseModel):
    """The scan job captures all sources and scan tasks for a scan."""

    JOB_RUN = 0
    JOB_TERMINATE_PAUSE = 1
    JOB_TERMINATE_CANCEL = 2
    JOB_TERMINATE_ACK = 3

    # all job types
    scan_type = models.CharField(
        max_length=12,
        choices=ScanTask.SCANTASK_TYPE_CHOICES,
        default=ScanTask.SCAN_TYPE_INSPECT,
    )
    status = models.CharField(
        max_length=20,
        choices=ScanTask.STATUS_CHOICES,
        default=ScanTask.CREATED,
    )
    status_message = models.TextField(
        null=True, default=_(messages.SJ_STATUS_MSG_CREATED)
    )
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    # all scan job types
    scan = models.ForeignKey(
        Scan, related_name="jobs", null=True, on_delete=models.SET_NULL
    )
    sources = models.ManyToManyField(Source)
    connection_results = models.OneToOneField(
        JobConnectionResult, null=True, on_delete=models.CASCADE
    )

    report = models.OneToOneField(Report, null=True, on_delete=models.CASCADE)

    objects = ScanJobQuerySet.as_manager()

    def __str__(self):
        """Get a rudimentary string representation."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, "
            f"scan_type={self.scan_type}, "
            f"status={self.status}"
            ")"
        )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_JOBS_MSG)
        ordering = ["-id"]

    @property
    def options(self):
        """Return the options property from the related Scan."""
        if self.scan:
            return self.scan.options
        return None

    @options.setter
    def options(self, value):
        """Set the options property for the related Scan."""
        if self.scan:
            self.scan.options = value
            self.scan.save()

    def get_extra_vars(self):
        """Return the extra vars from the related Scan."""
        if self.scan:
            return self.scan.get_extra_vars()
        return {}

    def copy_scan_details(self):
        """Copy scan details to the job."""
        scan = self.scan
        if scan is not None:
            self.sources.add(*scan.sources.all())
            self.scan_type = scan.scan_type
            self.save()

    def log_current_status(self, show_status_message=False, log_level=logging.INFO):
        """Log current status of task."""
        if show_status_message:
            message = (
                f"STATE UPDATE ({self.status})."
                f"  Additional State information: {self.status_message}"
            )
        else:
            message = f"STATE UPDATE ({self.status})"

        self.log_message(message, log_level=log_level)

    def log_message(self, message: str, log_level=logging.INFO):
        """
        Log a message for this job.

        TODO Rewrite this function to take a list of arguments instead of a string.
        Or kill this function and just use standard logger functionality.
        Variables in the message should be interpreted by standard logger functionality.
        """
        elapsed_time = self._compute_elapsed_time()
        actual_message = (
            f"Job {self.id:d} ({self.scan_type}, elapsed_time: {elapsed_time:.0f}s) - "
        )
        actual_message += message
        logger.log(log_level, actual_message)

    def calculate_counts(self):
        """Calculate scan counts from tasks.

        :return: systems_count, systems_scanned,
        systems_failed, systems_unreachable
        """
        self.refresh_from_db()
        if self.status in (ScanTask.CREATED, ScanTask.PENDING):
            return None, None, None, None, None

        system_fingerprint_count = 0

        (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
        ) = self._calculate_counts()

        self.refresh_from_db()
        if self.report_id and self.report:
            self.report.refresh_from_db()

            if self.report.deployment_report:
                system_fingerprint_count = (
                    self.report.deployment_report.system_fingerprints.count()
                )

        return (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
            system_fingerprint_count,
        )

    def _calculate_counts(self):
        """Calculate scan counts from tasks.

        :return: systems_count, systems_scanned,
        systems_failed, systems_unreachable
        """
        systems_sums = self.tasks.filter(scan_type=self.scan_type).aggregate(
            systems_count=Sum("systems_count"),
            systems_scanned=Sum("systems_scanned"),
            systems_failed=Sum("systems_failed"),
            systems_unreachable=Sum("systems_unreachable"),
        )
        # Need to handle None result as 0 if no tasks are found.
        return (
            systems_sums["systems_count"] or 0,
            systems_sums["systems_scanned"] or 0,
            systems_sums["systems_failed"] or 0,
            systems_sums["systems_unreachable"] or 0,
        )

    def _log_stats(self, prefix):
        """Log stats for scan."""
        (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
            system_fingerprint_count,
        ) = self.calculate_counts()

        message = (
            f"{prefix} Stats:"
            f" systems_count={systems_count:d},"
            f" systems_scanned={systems_scanned:d},"
            f" systems_failed={systems_failed:d},"
            f" systems_unreachable={systems_unreachable:d},"
            f" system_fingerprint_count={system_fingerprint_count:d}"
        )
        self.log_message(message)

    def _compute_elapsed_time(self):
        """Compute elapsed time."""
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (datetime.now(UTC) - self.start_time).total_seconds()
        return elapsed_time

    @transaction.atomic
    def queue(self):  # noqa: C901
        """Queue the job to run.

        Change job state from CREATED TO PENDING.
        """
        self.copy_scan_details()

        target_status = ScanTask.PENDING
        has_error = self.validate_status_change(target_status, [ScanTask.CREATED])
        if has_error:
            return

        if self.connection_results is None:
            job_conn_result = JobConnectionResult.objects.create()
            self.connection_results = job_conn_result
            self.save()

        if self.tasks:
            # It appears the initialization didn't complete
            # so remove partial results
            self.delete_inspect_results()
            self.tasks.all().delete()
            if self.connection_results is not None:
                self.connection_results.task_results.all().delete()
            if self.report and self.report.deployment_report:
                self.report.deployment_report.system_fingerprints.all().delete()

        # create tasks
        self._create_pending_tasks()

        if self.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
            # this job runs an actual scan
            if self.scan:
                self.scan.most_recent_scanjob = self
                self.scan.save()

            for source in self.sources.all():
                source.most_recent_connect_scan = self
                source.save()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_PENDING)
        self.save()
        self.log_current_status()

    def _create_pending_tasks(self):
        inspect_tasks = self._create_inspection_tasks()
        self._create_fingerprint_task(inspect_tasks)

    def delete_inspect_results(self, scan_task_id=None):
        """
        Delete InspectResults exclusively related to this ScanJob.

        Optionally filter to delete only the InspectResults related to
        the given ScanTask ID.
        """
        filters = Q(inspect_group__tasks__job_id=self.id)
        if scan_task_id:
            filters = filters & Q(inspect_group__tasks__in=[scan_task_id])
        InspectResult.objects.filter(filters).exclude(
            inspect_group__reports__scanjob__in=ScanJob.objects.exclude(id=self.id)
        ).delete()
        # cleanup orphan InspectGroups
        InspectGroup.objects.exclude(
            inspect_results__in=InspectResult.objects.all()
        ).delete()

    def _create_inspection_tasks(self):
        """Create initial inspection tasks.

        :return: list of inspection_tasks
        """
        if self.scan_type != ScanTask.SCAN_TYPE_INSPECT:
            return []
        inspect_tasks = []
        # TODO Remove the index/count-based sequence_number.
        # Relying on the index/count to drive sequence_number is a brittle kludge.
        # Inspect tasks should be asynchronous, not needing a sequence or order.
        for index, source in enumerate(self.sources.all()):
            # Note: We create a TaskConnectionResult with each inspect-type ScanTask.
            # This is an artifact from an old design where the acts of connecting to a
            # source and inspecting that source were two wholly separate operations.
            # However, at the time of this writing, we are mid-refactor of simplifying
            # the inspection process, and we still store TaskConnectionResults just
            # before we perform the actual inspection.
            # TODO remove connection_result and TaskConnectionResult.
            inspect_task = ScanTask.objects.create(
                job=self,
                source=source,
                scan_type=ScanTask.SCAN_TYPE_INSPECT,
                status=ScanTask.PENDING,
                status_message=_(messages.ST_STATUS_MSG_PENDING),
                sequence_number=index,
                connection_result=TaskConnectionResult.objects.create(
                    job_connection_result=self.connection_results
                ),
            )
            inspect_tasks.append(inspect_task)
            self.tasks.add(inspect_task)

        return inspect_tasks

    def _create_fingerprint_task(self, inspect_tasks):
        """Create initial inspection tasks.

        :param inspect_tasks: list of inspection tasks
        """
        if self.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT or inspect_tasks:
            # TODO Remove this len/count-based sequence_number.
            # Relying on the count to drive sequence_number is a brittle kludge.
            # The fingerprint task should simply run after all inspect tasks,
            # regardless of how many inspect tasks preceded it.
            sequence_number = len(inspect_tasks) + 1
            # Create a single fingerprint task with dependencies
            fingerprint_task = ScanTask.objects.create(
                job=self,
                scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                status=ScanTask.PENDING,
                status_message=_(messages.ST_STATUS_MSG_PENDING),
                sequence_number=sequence_number,
            )
            fingerprint_task.prerequisites.set(inspect_tasks)

            self.tasks.add(fingerprint_task)
            return fingerprint_task

    def status_start(self):
        """Change status from PENDING to RUNNING.

        :returns: bool True if successfully updated, else False
        """
        self.start_time = datetime.now(UTC)
        target_status = ScanTask.RUNNING
        has_error = self.validate_status_change(target_status, [ScanTask.PENDING])
        if has_error:
            return False

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
        self.save()
        self.log_current_status()
        return True

    def status_restart(self):
        """Change status from PENDING/PAUSED/RUNNING to PENDING.

        :returns: bool True if successfully updated, else False
        """
        target_status = ScanTask.PENDING
        has_error = self.validate_status_change(
            target_status, [ScanTask.PENDING, ScanTask.PAUSED, ScanTask.RUNNING]
        )
        if has_error:
            return False
        # Update tasks
        paused_tasks = self.tasks.filter(Q(status=ScanTask.PAUSED))
        if paused_tasks:
            for task in paused_tasks:
                task.status_restart()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
        self.save()
        self.log_current_status()
        return True

    @transaction.atomic
    def status_pause(self):
        """Change status from PENDING/RUNNING to PAUSED.

        :returns: bool True if successfully updated, else False
        """
        target_status = ScanTask.PAUSED
        has_error = self.validate_status_change(
            target_status, [ScanTask.PENDING, ScanTask.RUNNING]
        )
        if has_error:
            return False

        # Update tasks
        tasks_to_pause = self.tasks.exclude(
            Q(status=ScanTask.FAILED)
            | Q(status=ScanTask.CANCELED)
            | Q(status=ScanTask.COMPLETED)
        )
        if tasks_to_pause:
            for task in tasks_to_pause:
                task.status_pause()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_PAUSED)
        self.save()
        self.log_current_status()
        return True

    @transaction.atomic
    def status_cancel(self):
        """Change status from CREATED/PENDING/RUNNING/PAUSED to CANCELED.

        :returns: bool True if successfully updated, else False
        """
        self.end_time = datetime.now(UTC)
        target_status = ScanTask.CANCELED
        has_error = self.validate_status_change(
            target_status,
            [ScanTask.CREATED, ScanTask.PENDING, ScanTask.RUNNING, ScanTask.PAUSED],
        )
        if has_error:
            return False

        # Update tasks
        tasks_to_cancel = self.tasks.exclude(
            Q(status=ScanTask.FAILED)
            | Q(status=ScanTask.CANCELED)
            | Q(status=ScanTask.COMPLETED)
        )
        if tasks_to_cancel:
            for task in tasks_to_cancel:
                task.status_cancel()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_CANCELED)
        self.save()
        self.log_current_status()
        return True

    def status_complete(self):
        """Change status from RUNNING to COMPLETE.

        :returns: bool True if successfully updated, else False
        """
        self.end_time = datetime.now(UTC)
        target_status = ScanTask.COMPLETED
        has_error = self.validate_status_change(target_status, [ScanTask.RUNNING])
        if has_error:
            return False

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_COMPLETED)
        self.save()
        self._log_stats("COMPLETION STATS.")
        self.log_current_status()
        return True

    def status_fail(self, message):
        """Change status from RUNNING to FAILED.

        :param message: The error message associated with failure
        :returns: bool True if successfully updated, else False
        """
        self.end_time = datetime.now(UTC)
        target_status = ScanTask.FAILED
        has_error = self.validate_status_change(target_status, [ScanTask.RUNNING])
        if has_error:
            return False

        self.status = target_status
        self.status_message = message
        self.log_message(self.status_message, log_level=logging.ERROR)
        self.save()
        self._log_stats("FAILURE STATS.")
        self.log_current_status(show_status_message=True, log_level=logging.ERROR)
        return True

    def validate_status_change(self, target_status, valid_current_status):
        """Validate and transition job status.

        :param target_status: Desired transition state
        :param valid_current_status: List of compatible current
        states for transition
        :returns bool indicating if it was successful:
        """
        if target_status == self.status:
            self.log_message(
                f"ScanJob status is already {target_status}", log_level=logging.DEBUG
            )
            return False

        if self.status not in valid_current_status:
            self.log_message(
                f"Cannot change job state to {target_status} when it is {self.status}",
                log_level=logging.ERROR,
            )
            return True
        return False

    def ingest_sources(self, source_list, task_sequence_number=1):
        """Create raw facts associated to this job."""
        # TODO: adjust this method (or create a new one) for v2 api "raw facts" format.
        # This method will be problematic for source_lists containing thousands
        # of entries. We might keep it in the future, but consider invoking it in small
        # chunks.
        report = self.report or Report.objects.create(scanjob=self)
        inspect_group_list = []
        inspect_result_list = []
        raw_fact_list = []
        for source_dict in source_list:
            inspect_group = InspectGroup(
                source_type=source_dict["source_type"],
                source_name=source_dict["source_name"],
                server_id=source_dict["server_id"],
                server_version=source_dict["report_version"],
            )
            inspect_group_list.append(inspect_group)
            for fact_dict in source_dict["facts"]:
                # InspectResult is lacking 'name' and 'status'. While
                # 'details report' isn't modified (or replaced), there's
                # nothing we can do.
                # TODO: make this non optional for v2 equivalent
                inspect_result = InspectResult(inspect_group=inspect_group)
                inspect_result_list.append(inspect_result)
                raw_fact_list.extend(
                    RawFact(name=k, value=v, inspect_result=inspect_result)
                    for k, v in fact_dict.items()
                )
        InspectGroup.objects.bulk_create(
            inspect_group_list, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        InspectResult.objects.bulk_create(
            inspect_result_list, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        RawFact.objects.bulk_create(
            raw_fact_list, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        report.inspect_groups.set(inspect_group_list)

    def copy_raw_facts_from_reports(self, report_id_list, task_sequence_number=1):
        """Create raw facts associated to this job."""
        inspect_groups = InspectGroup.objects.filter(
            reports__id__in=report_id_list,
        ).all()
        self.report.inspect_groups.set(inspect_groups)
