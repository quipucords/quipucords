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
import json
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models import Q
from rest_framework.serializers import ValidationError
from api.source.model import Source
from api.scantasks.model import ScanTask
from api.connresults.model import ConnectionResults
from api.inspectresults.model import InspectionResults
import api.messages as messages

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan job."""

    max_concurrency = models.PositiveIntegerField(default=50)
    disable_optional_products = models.TextField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'max_concurrency: {}, '\
            'disable_optional_products:' \
                     ' {}'.format(self.id,
                                  self.max_concurrency,
                                  self.disable_optional_products)\
            + '}'


class ScanJob(models.Model):
    """The scan job captures all sources and scan tasks for a scan."""

    JBOSS_EAP = 'jboss_eap'
    JBOSS_FUSE = 'jboss_fuse'
    JBOSS_BRMS = 'jboss_brms'

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
    fact_collection_id = models.IntegerField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'sources:{}, '\
            'scan_type:{}, '\
            'status:{}, '\
            'tasks: {}, '\
            'options: {}, '\
            'fact_collection_id: {}'.format(self.id,
                                            self.sources,
                                            self.scan_type,
                                            self.status,
                                            self.tasks,
                                            self.options,
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
                                 status_message=_(
                                     messages.ST_STATUS_MSG_PENDING),
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
                                        status_message=_(
                                            messages.ST_STATUS_MSG_PENDING),
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
        self.status_message = _(messages.SJ_STATUS_MSG_PENDING)
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
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
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
                task.restart()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_RUNNING)
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
                task.pause()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_PAUSED)
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
                task.cancel()

        self.status = target_status
        self.status_message = _(messages.SJ_STATUS_MSG_CANCELED)
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
        self.status_message = _(messages.SJ_STATUS_MSG_COMPLETED)
        self.save()

    def fail(self, message):
        """Fail a job.

        Change job state from RUNNING TO COMPLETE.
        :param message: The error message associated with failure
        """
        target_status = ScanTask.FAILED
        has_error = self.validate_status_change(target_status,
                                                [ScanTask.RUNNING])
        if has_error:
            return

        self.status = target_status
        self.status_message = message
        logger.error(self.status_message)
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

    def validate_extra_vars(self):
        """Make sure that extra vars are a dictionary with boolean values.

        :return extra_vars if no ValidationErrors are raised
        """
        extra_vars = self.get_optional_products_args()
        if not isinstance(extra_vars, dict):
            raise ValidationError(_(messages.SJ_EXTRA_VARS_DICT))
        for key in extra_vars:
            if not isinstance(extra_vars[key], bool):
                raise ValidationError(_(messages.SJ_EXTRA_VARS_BOOL))
            elif key not in [ScanJob.JBOSS_EAP,
                             ScanJob.JBOSS_BRMS,
                             ScanJob.JBOSS_FUSE]:
                raise ValidationError(_(messages.SJ_EXTRA_VARS_KEY))
        return extra_vars

    def create_extra_vars(self):
        """Construct a dictionary based on the disabled products.

        :returns: a dictionary representing the updated collection
        status of the optional products to be assigned as the extra
        vars for the ansibile task runner
        """
        # Grab the optional products status dict and create
        # a default dict (all products default to True)
        product_status = self.validate_extra_vars()
        product_default = {self.JBOSS_EAP: True,
                           self.JBOSS_FUSE: True,
                           self.JBOSS_BRMS: True}

        if product_status == {}:
            return product_default
        # If specified, turn off fact collection for fuse
        if product_status.get(self.JBOSS_FUSE) is False:
            product_default[self.JBOSS_FUSE] = False
        # If specified, turn off fact collection for brms
        if product_status.get(self.JBOSS_BRMS) is False:
            product_default[self.JBOSS_BRMS] = False
        # If specified and both brms & fuse are false
        # turn off fact collection for eap
        if product_status.get(self.JBOSS_EAP) is False and \
                (not product_default.get(self.JBOSS_FUSE)) and \
                (not product_default.get(self.JBOSS_BRMS)):
            product_default[self.JBOSS_EAP] = False

        return product_default

    def get_optional_products_args(self):
        """Access disabled_optional_products as a dict instead of a string.

        :returns: python dict containing the status of optional products
        """
        if self.options.disable_optional_products is not None:
            if isinstance(self.options.disable_optional_products, dict):
                return self.options.disable_optional_products
            return json.loads(self.options.disable_optional_products)
        return {}
