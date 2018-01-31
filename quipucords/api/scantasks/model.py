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
from api.source.model import Source
import api.messages as messages

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanTask(models.Model):
    """The scan task captures a single source for a scan."""

    SCAN_TYPE_CONNECT = 'connect'
    SCAN_TYPE_INSPECT = 'inspect'
    SCAN_TYPE_CHOICES = ((SCAN_TYPE_CONNECT, SCAN_TYPE_CONNECT),
                         (SCAN_TYPE_INSPECT, SCAN_TYPE_INSPECT))

    CREATED = 'created'
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    CANCELED = 'canceled'
    COMPLETED = 'completed'
    FAILED = 'failed'
    STATUS_CHOICES = ((CREATED, CREATED),
                      (PENDING, PENDING),
                      (RUNNING, RUNNING),
                      (PAUSED, PAUSED),
                      (COMPLETED, COMPLETED),
                      (CANCELED, CANCELED),
                      (FAILED, FAILED))

    # Model fields
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    scan_type = models.CharField(
        max_length=9,
        choices=SCAN_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    status_message = models.CharField(
        max_length=256, null=True, default=_(messages.ST_STATUS_MSG_PENDING))
    prerequisites = models.ManyToManyField('ScanTask')
    systems_count = models.PositiveIntegerField(null=True)
    systems_scanned = models.PositiveIntegerField(null=True)
    systems_failed = models.PositiveIntegerField(null=True)
    sequence_number = models.PositiveIntegerField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'scan_type:{}, '\
            'status:{}, '\
            'source:{}, '\
            'sequence_number:{}, '\
            'systems_count: {}, '\
            'systems_scanned: {}, '\
            'systems_failed: {}, '\
            'start_time: {} '\
            'end_time: {} '.format(self.id,
                                   self.scan_type,
                                   self.status,
                                   self.source,
                                   self.sequence_number,
                                   self.systems_count,
                                   self.systems_scanned,
                                   self.systems_failed,
                                   self.start_time,
                                   self.end_time) + '}'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_TASKS_MSG)

    def start(self):
        """Start a task."""
        self.status = ScanTask.RUNNING
        self.status_message = _(messages.ST_STATUS_MSG_RUNNING)
        self.save()

    def restart(self):
        """Start a task."""
        self.status = ScanTask.PENDING
        self.status_message = 'Task was restarted'
        self.save()

    def pause(self):
        """Pause a task."""
        self.status = ScanTask.PAUSED
        self.status_message = _(messages.ST_STATUS_MSG_PAUSED)
        self.save()

    def cancel(self):
        """Cancel a task."""
        self.status = ScanTask.CANCELED
        self.status_message = _(messages.ST_STATUS_MSG_CANCELED)
        self.save()

    def complete(self, message=None):
        """Complete a task."""
        self.status = ScanTask.COMPLETED
        if message:
            self.status_message = message
            logger.info(self.status_message)
        else:
            self.status_message = _(messages.ST_STATUS_MSG_COMPLETED)
        self.save()

    def fail(self, message):
        """Fail a task.

        :param message: The error message associated with failure
        """
        self.status = ScanTask.FAILED
        self.status_message = message
        logger.error(self.status_message)
        self.save()
