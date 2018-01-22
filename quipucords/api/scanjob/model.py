#
# Copyright (c) 2017 Red Hat, Inc.
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
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models import Q
from api.source.model import Source
from api.scantasks.model import ScanTask
from api.connresults.model import ConnectionResults
from api.inspectresults.model import InspectionResults
import api.messages as messages

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan job."""

    # Scan Options
    SCAN_JBOSS_EAP = 'jboss-eap'
    SCAN_JBOSS_FUSE = 'jboss-fuse'
    SCAN_JBOSS_BRMS = 'jboss-brms'
    # SCAN_EAP_FUSE = [SCAN_JBOSS_EAP, SCAN_JBOSS_FUSE]
    # SCAN_EAP_BRMS = 'jboss-eap', 'jboss-brms'
    # SCAN_EAP_FUSE_BRMS = 'jboss-eap', 'jboss-fuse', 'jboss-brms'
    SCAN_CHOICES = ((SCAN_JBOSS_EAP, SCAN_JBOSS_EAP),
                    (SCAN_JBOSS_FUSE, SCAN_JBOSS_FUSE),
                    (SCAN_JBOSS_BRMS, SCAN_JBOSS_BRMS))
                    # (SCAN_EAP_FUSE, SCAN_EAP_FUSE),
                    # (SCAN_EAP_BRMS, SCAN_EAP_BRMS),
                    # (SCAN_EAP_FUSE_BRMS, SCAN_EAP_FUSE_BRMS))

    optional_products = models.CharField(
        max_length=50,
        choices=SCAN_CHOICES,
        null=True
    )
    max_concurrency = models.PositiveIntegerField(default=50)

    def __str__(self):
        """Convert to string."""
        print('\n\n\n Optional Products: \n\n\n')
        print(self.optional_products)
        print('\n\n\n')
        return '{' + 'id:{}, '\
            'max_concurrency: {}, '\
            'optional_products: {}'.format(self.id,
                                           self.max_concurrency,
                                           self.optional_products) \
            + '}'


class ScanJob(models.Model):
    """The scan job captures all sources and scan tasks for a scan."""

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
    tasks = models.ManyToManyField(ScanTask)
    options = models.ForeignKey(
        ScanOptions, null=True, on_delete=models.CASCADE)
    SCAN_JBOSS_EAP = 'jboss-eap'
    SCAN_JBOSS_FUSE = 'jboss-fuse'
    SCAN_JBOSS_BRMS = 'jboss-brms'
    # SCAN_EAP_FUSE = [SCAN_JBOSS_EAP, SCAN_JBOSS_FUSE]
    # SCAN_EAP_BRMS = ['jboss-eap', 'jboss-brms']
    # SCAN_EAP_FUSE_BRMS = ['jboss-eap', 'jboss-fuse', 'jboss-brms']
    SCAN_CHOICES = ((SCAN_JBOSS_EAP, SCAN_JBOSS_EAP),
                    (SCAN_JBOSS_FUSE, SCAN_JBOSS_FUSE),
                    (SCAN_JBOSS_BRMS, SCAN_JBOSS_BRMS))
                    # (SCAN_EAP_FUSE, SCAN_EAP_FUSE),
                    # (SCAN_EAP_BRMS, SCAN_EAP_BRMS),
                    # (SCAN_EAP_FUSE_BRMS, SCAN_EAP_FUSE_BRMS))

    optional_products = models.CharField(
        max_length=10,
        choices=SCAN_CHOICES,
        null=True
    )
    fact_collection_id = models.IntegerField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'sources:{}, '\
            'scan_type:{}, '\
            'status:{}, '\
            'tasks: {}, '\
            'options: {}, '\
            'optional_products: {}, '\
            'fact_collection_id: {}'.format(self.id,
                                            self.sources,
                                            self.scan_type,
                                            self.status,
                                            self.tasks,
                                            self.options,
                                            self.optional_products,
                                            self.fact_collection_id) + '}'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_JOBS_MSG)

    def queue(self):
        """Queue the job to run.

        Change job state from CREATED TO PENDING.
        """
        # pylint: disable=no-member
        target_status = ScanTask.PENDING
        has_error = self.validate_status_change(
            target_status, [ScanTask.CREATED])
        if has_error:
            return

        if self.tasks:
            # It appears the initialization didn't complete
            # so remove partial results
            self.tasks.all().delete()
            ConnectionResults.objects.filter(
                scan_job=self.id).delete()
            InspectionResults.objects.filter(
                scan_job=self.id).delete()

        job_scan_type = self.scan_type
        count = 0
        conn_tasks = []
        for source in self.sources.all():
            conn_task = ScanTask(source=source,
                                 scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                 status=ScanTask.PENDING,
                                 sequence_number=count)
            conn_task.save()
            self.tasks.add(conn_task)
            conn_tasks.append(conn_task)

            count += 1

        if job_scan_type == ScanTask.SCAN_TYPE_INSPECT:
            for conn_task in conn_tasks:
                inspect_task = ScanTask(source=conn_task.source,
                                        scan_type=ScanTask.SCAN_TYPE_INSPECT,
                                        status=ScanTask.PENDING,
                                        sequence_number=count)
                inspect_task.save()
                inspect_task.prerequisites.add(conn_task)
                inspect_task.save()

                self.tasks.add(inspect_task)

                count += 1

        # Setup results objects
        temp_conn_results = ConnectionResults(scan_job=self)
        temp_conn_results.save()

        if job_scan_type == ScanTask.SCAN_TYPE_INSPECT:
            temp_inspect_results = InspectionResults(scan_job=self)
            temp_inspect_results.save()

        self.status = target_status
        self.save()

    def start(self):
        """Start a job.

        Change job state from PENDING TO RUNNING.
        """
        target_status = ScanTask.RUNNING
        has_error = self.validate_status_change(
            target_status, [ScanTask.PENDING])
        if has_error:
            return

        self.status = target_status
        self.save()

    def restart(self):
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
                task.status = ScanTask.PENDING
                task.save()

        self.status = target_status
        self.save()

    def pause(self):
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
                task.status = ScanTask.PAUSED
                task.save()

        self.status = target_status
        self.save()

    def cancel(self):
        """Cancel a job.

        Change job state from CREATED, PENDING, RUNNING, or
        PAUSED to CANCELED.
        """
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
                task.status = ScanTask.CANCELED
                task.save()

        self.status = target_status
        self.save()

    def complete(self):
        """Complete a job.

        Change job state from RUNNING TO COMPLETE.
        """
        target_status = ScanTask.COMPLETED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.RUNNING])
        if has_error:
            return

        self.status = target_status
        self.save()

    def fail(self):
        """Fail a job.

        Change job state from RUNNING TO COMPLETE.
        """
        target_status = ScanTask.FAILED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.RUNNING])
        if has_error:
            return

        self.status = target_status
        self.save()

    def validate_status_change(self, target_status, valid_current_status):
        """Validate and transition job status.

        :param target_status: Desired transition state
        :param valid_current_status: List of compatible current
        states for transition
        :returns bool indicating if it was successful:
        """
        if target_status == self.status:
            logger.debug('ScanJob status is already %s', target_status)
            return False

        if self.status not in valid_current_status:
            logger.error('Cannot change job state to %s when it is %s',
                         target_status, self.status)
            return True
        return False
