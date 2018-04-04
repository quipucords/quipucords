#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Defines the models used with the API application.

These models are used in the REST definitions.
"""
import logging
from datetime import datetime

import api.messages as messages
from api.connresults.model import (JobConnectionResult,
                                   TaskConnectionResult)
from api.inspectresults.model import (JobInspectionResult,
                                      TaskInspectionResult)
from api.scan.model import Scan, ScanOptions
from api.scantasks.model import ScanTask
from api.source.model import Source

from django.db import (OperationalError, models, transaction)
from django.db.models import Q
from django.utils.translation import ugettext as _

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJob(models.Model):
    """The scan job captures all sources and scan tasks for a scan."""

    # pylint: disable=too-many-instance-attributes
    scan = models.ForeignKey(Scan, related_name='jobs', null=True)
    sources = models.ManyToManyField(Source)
    scan_type = models.CharField(
        max_length=9,
        choices=ScanTask.SCAN_TYPE_CHOICES,
        default=ScanTask.SCAN_TYPE_INSPECT,
    )
    status = models.CharField(
        max_length=20,
        choices=ScanTask.STATUS_CHOICES,
        default=ScanTask.CREATED,
    )
    status_message = models.CharField(
        max_length=256,
        null=True,
        default=_(messages.SJ_STATUS_MSG_CREATED))
    tasks = models.ManyToManyField(ScanTask)
    options = models.ForeignKey(
        ScanOptions, null=True, on_delete=models.CASCADE)
    report_id = models.IntegerField(null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    connection_results = models.ForeignKey(
        JobConnectionResult, null=True, on_delete=models.CASCADE)
    inspection_results = models.ForeignKey(
        JobInspectionResult, null=True, on_delete=models.CASCADE)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'scan:{}, '\
            'sources:{}, '\
            'scan_type:{}, '\
            'status:{}, '\
            'tasks: {}, '\
            'options: {}, '\
            'report_id: {}, '\
            'start_time: {}, '\
            'end_time: {}, '\
            'connection_results: {}, '\
            'inspection_results: {}'.format(self.id,
                                            self.scan,
                                            self.sources,
                                            self.scan_type,
                                            self.status,
                                            self.tasks,
                                            self.options,
                                            self.report_id,
                                            self.start_time,
                                            self.end_time,
                                            self.connection_results,
                                            self.inspection_results) + '}'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_JOBS_MSG)
        ordering = ['-id']

    def copy_scan_configuration(self):
        """Copy scan info into the job."""
        # pylint: disable=no-member
        scan = self.scan
        if scan is not None:
            for source in scan.sources.all():
                self.sources.add(source)
            self.scan_type = scan.scan_type
            if scan.options is not None:
                disable_options = scan.options.disabled_optional_products
                extended_search = scan.options.enabled_extended_product_search
                scan_job_options = ScanOptions(
                    max_concurrency=scan.options.max_concurrency,
                    disabled_optional_products=disable_options,
                    enabled_extended_product_search=extended_search)
                scan_job_options.save()
                self.options = scan_job_options
            self.save()

    def log_current_status(self,
                           show_status_message=False,
                           log_level=logging.INFO):
        """Log current status of task."""
        if show_status_message:
            message = 'STATE UPDATE (%s).'\
                '  Additional State information: %s' %\
                (self.status,
                 self.status_message)
        else:
            message = 'STATE UPDATE (%s)' %\
                (self.status)

        self.log_message(message, log_level=log_level)

    def log_message(self, message, log_level=logging.INFO):
        """Log a message for this job."""
        elapsed_time = self._compute_elapsed_time()
        actual_message = 'Job %d (%s, elapsed_time: %ds) - ' % \
            (self.id,
             self.scan_type,
             elapsed_time)
        actual_message += message
        logger.log(log_level, actual_message)

    def calculate_counts(self, connect_only=False):
        """Calculate scan counts from tasks.

        :param connect_only: counts should only include
        connection scan results
        :return: systems_count, systems_scanned, systems_failed
        """
        if self.status == ScanTask.CREATED or \
                self.status == ScanTask.PENDING:
            return None, None, None, None

        systems_count = 0
        systems_scanned = 0
        systems_failed = 0
        systems_unreachable = 0

        connection_systems_count,\
            connection_systems_scanned,\
            connection_systems_failed,\
            connection_systems_unreachable = self._calculate_counts(
                ScanTask.SCAN_TYPE_CONNECT)
        if self.scan_type == ScanTask.SCAN_TYPE_CONNECT or connect_only:
            systems_count = connection_systems_count
            systems_scanned = connection_systems_scanned
            systems_failed = connection_systems_failed
            systems_unreachable = connection_systems_unreachable
        else:
            _,\
                inspect_systems_scanned,\
                inspect_systems_failed,\
                inspect_systems_unreachable = self._calculate_counts(
                    ScanTask.SCAN_TYPE_INSPECT)
            systems_count = connection_systems_count
            systems_scanned = inspect_systems_scanned
            systems_failed = inspect_systems_failed + connection_systems_failed
            systems_unreachable = \
                inspect_systems_unreachable + connection_systems_unreachable
        return systems_count,\
            systems_scanned, \
            systems_failed, \
            systems_unreachable

    def _calculate_counts(self, scan_type):
        """Calculate scan counts from tasks.

        :return: systems_count, systems_scanned, systems_failed
        """
        systems_count = 0
        systems_scanned = 0
        systems_failed = 0
        systems_unreachable = 0
        tasks = self.tasks.filter(
            scan_type=scan_type).order_by('sequence_number')
        for task in tasks:
            if task.systems_count is not None:
                if systems_count is None:
                    systems_count = 0
                systems_count += task.systems_count
            if task.systems_scanned is not None:
                if systems_scanned is None:
                    systems_scanned = 0
                systems_scanned += task.systems_scanned
            if task.systems_failed is not None:
                if systems_failed is None:
                    systems_failed = 0
                systems_failed += task.systems_failed
            if task.systems_unreachable is not None:
                if systems_unreachable is None:
                    systems_unreachable = 0
                systems_unreachable += task.systems_unreachable
        return systems_count,\
            systems_scanned,\
            systems_failed,\
            systems_unreachable

    def _log_stats(self, prefix):
        """Log stats for scan."""
        systems_count,\
            systems_scanned,\
            systems_failed,\
            systems_unreachable = self._calculate_counts(
                ScanTask.SCAN_TYPE_CONNECT)

        message = '%s Stats: systems_count=%d,'\
            ' systems_scanned=%d, systems_failed=%d, systems_unreachable=%d' %\
            (prefix,
             systems_count,
             systems_scanned,
             systems_failed,
             systems_unreachable)
        self.log_message(message)

    def _compute_elapsed_time(self):
        """Compute elapsed time."""
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (datetime.utcnow() -
                            self.start_time).total_seconds()
        return elapsed_time

    def safe_state_change(self, method_name, message=None):
        """Update state in protected clause."""
        # django.db.utils.OperationalError: database is locked
        try:
            method = getattr(self, method_name)
            if method_name == '_fail':
                method(message)
            else:
                method()
        except OperationalError:
            # try one more time
            method = getattr(self, method_name)
            if method_name == '_fail':
                method(message)
            else:
                method()

    def queue(self):
        """Queue the job to run.

        Change job state from CREATED TO PENDING.
        """
        self.safe_state_change('_queue')

    @transaction.atomic
    def _queue(self):
        """Queue the job to run.

        Change job state from CREATED TO PENDING.
        """
        # pylint: disable=no-member,too-many-statements
        self.copy_scan_configuration()

        target_status = ScanTask.PENDING
        has_error = self.validate_status_change(
            target_status, [ScanTask.CREATED])
        if has_error:
            return

        if self.connection_results is None:
            job_conn_result = JobConnectionResult()
            job_conn_result.save()
            self.connection_results = job_conn_result
            self.save()
        if self.inspection_results is None and \
                self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            job_inspect_result = JobInspectionResult()
            job_inspect_result.save()
            self.inspection_results = job_inspect_result
            self.save()

        if self.tasks:
            # It appears the initialization didn't complete
            # so remove partial results
            self.tasks.all().delete()
            if self.connection_results is not None:
                self.connection_results.task_results.all().delete()
            if self.inspection_results is not None:
                self.inspection_results.task_results.all().delete()

        count = 0
        conn_tasks = []
        for source in self.sources.all():
            # Create connect tasks
            conn_task = ScanTask(source=source,
                                 scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                 status=ScanTask.PENDING,
                                 status_message=_(
                                     messages.ST_STATUS_MSG_PENDING),
                                 sequence_number=count)
            conn_task.save()
            self.tasks.add(conn_task)
            conn_tasks.append(conn_task)

            # Create task result
            conn_task_result = TaskConnectionResult()
            conn_task_result.save()

            # Add the task result to job results
            self.connection_results.task_results.add(conn_task_result)
            self.connection_results.save()

            # Add the task result to task
            conn_task.connection_result = conn_task_result
            conn_task.save()

            count += 1

        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            for conn_task in conn_tasks:
                # Create inspect tasks
                inspect_task = ScanTask(source=conn_task.source,
                                        scan_type=ScanTask.SCAN_TYPE_INSPECT,
                                        status=ScanTask.PENDING,
                                        status_message=_(
                                            messages.ST_STATUS_MSG_PENDING),
                                        sequence_number=count)
                inspect_task.save()
                inspect_task.prerequisites.add(conn_task)
                inspect_task.save()
                self.tasks.add(inspect_task)

                # Create task result
                inspect_task_result = TaskInspectionResult()
                inspect_task_result.save()

                # Add the task result to job results
                self.inspection_results.task_results.add(inspect_task_result)
                self.inspection_results.save()

                # Add the inspect task result to task
                inspect_task.inspection_result = inspect_task_result
                inspect_task.save()

                count += 1

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

    def start(self):
        """Start a job.

        Change job state from PENDING TO RUNNING.
        """
        self.safe_state_change('_start')

    @transaction.atomic
    def _start(self):
        """Start a job.

        Change job state from PENDING TO RUNNING.
        """
        self.start_time = datetime.utcnow()
        target_status = ScanTask.RUNNING
        has_error = self.validate_status_change(
            target_status, [ScanTask.PENDING])
        if has_error:
            return

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
        self.save()
        self.log_current_status()

    def restart(self):
        """Restart a job.

        Change job state from PENDING, PAUSED OR RUNNING
        TO RUNNING status. Handles job that need to be run,
        jobs that were running and the server quick, and
        paused jobs.
        """
        self.safe_state_change('_restart')

    @transaction.atomic
    def _restart(self):
        """Restart a job.

        Change job state from PENDING, PAUSED OR RUNNING
        TO RUNNING status. Handles job that need to be run,
        jobs that were running and the server quick, and
        paused jobs.
        """
        target_status = ScanTask.RUNNING
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.PENDING,
                                                 ScanTask.PAUSED,
                                                 ScanTask.RUNNING])
        if has_error:
            return
        # Update tasks
        paused_tasks = self.tasks.filter(Q(status=ScanTask.PAUSED))
        if paused_tasks:
            for task in paused_tasks:
                task.restart()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
        self.save()
        self.log_current_status()

    def pause(self):
        """Pause a job.

        Change job state from PENDING/RUNNING TO PAUSED.
        """
        self.safe_state_change('_pause')

    @transaction.atomic
    def _pause(self):
        """Pause a job.

        Change job state from PENDING/RUNNING TO PAUSED.
        """
        target_status = ScanTask.PAUSED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.PENDING,
                                                 ScanTask.RUNNING])
        if has_error:
            return

        # Update tasks
        tasks_to_pause = self.tasks.exclude(Q(status=ScanTask.FAILED) |
                                            Q(status=ScanTask.CANCELED) |
                                            Q(status=ScanTask.COMPLETED))
        if tasks_to_pause:
            for task in tasks_to_pause:
                task.pause()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_PAUSED)
        self.save()
        self.log_current_status()

    def cancel(self):
        """Cancel a job.

        Change job state from CREATED, PENDING, RUNNING, or
        PAUSED to CANCELED.
        """
        self.safe_state_change('_cancel')

    @transaction.atomic
    def _cancel(self):
        """Cancel a job.

        Change job state from CREATED, PENDING, RUNNING, or
        PAUSED to CANCELED.
        """
        self.end_time = datetime.utcnow()
        target_status = ScanTask.CANCELED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.CREATED,
                                                 ScanTask.PENDING,
                                                 ScanTask.RUNNING,
                                                 ScanTask.PAUSED])
        if has_error:
            return

        # Update tasks
        tasks_to_cancel = self.tasks.exclude(
            Q(status=ScanTask.FAILED) |
            Q(status=ScanTask.CANCELED) |
            Q(status=ScanTask.COMPLETED))
        if tasks_to_cancel:
            for task in tasks_to_cancel:
                task.cancel()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_CANCELED)
        self.save()
        self.log_current_status()

    def complete(self):
        """Complete a job.

        Change job state from RUNNING TO COMPLETE.
        """
        self.safe_state_change('_complete')

    @transaction.atomic
    def _complete(self):
        """Complete a job.

        Change job state from RUNNING TO COMPLETE.
        """
        self.end_time = datetime.utcnow()
        target_status = ScanTask.COMPLETED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.RUNNING])
        if has_error:
            return

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_COMPLETED)
        self.save()
        self._log_stats('COMPLETION STATS.')
        self.log_current_status()

    def fail(self, message):
        """Fail a job.

        Change job state from RUNNING TO COMPLETE.
        :param message: The error message associated with failure
        """
        self.safe_state_change('_fail', message)

    @transaction.atomic
    def _fail(self, message):
        """Fail a job.

        Change job state from RUNNING TO COMPLETE.
        :param message: The error message associated with failure
        """
        self.end_time = datetime.utcnow()
        target_status = ScanTask.FAILED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.RUNNING])
        if has_error:
            return

        self.status = target_status
        self.status_message = message
        self.log_message(self.status_message, log_level=logging.ERROR)
        self.save()
        self._log_stats('FAILURE STATS.')
        self.log_current_status(show_status_message=True,
                                log_level=logging.ERROR)

    def validate_status_change(self, target_status, valid_current_status):
        """Validate and transition job status.

        :param target_status: Desired transition state
        :param valid_current_status: List of compatible current
        states for transition
        :returns bool indicating if it was successful:
        """
        if target_status == self.status:
            self.log_message('ScanJob status is already %s' %
                             target_status, log_level=logging.DEBUG)
            return False

        if self.status not in valid_current_status:
            self.log_message('Cannot change job state to %s when it is %s' %
                             (target_status, self.status),
                             log_level=logging.ERROR)
            return True
        return False
