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
from datetime import datetime
import logging
from django.db import transaction
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
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

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

    def log_current_status(self,
                           show_status_message=False,
                           log_level=logging.INFO):
        """Log current status of task."""
        if show_status_message:
            message = 'STATE UPDATE (%s).  '\
                'Additional status information: %s' %\
                (self.status,
                 self.status_message)
        else:
            message = 'STATE UPDATE (%s)' %\
                (self.status)
        self.log_message(message, log_level=log_level)

    def _log_stats(self, prefix):
        """Log stats for scan."""
        sys_count = self.systems_count
        sys_failed = self.systems_failed
        sys_scanned = self.systems_scanned
        if sys_count is None:
            sys_count = 0
        if sys_scanned is None:
            sys_scanned = 0
        if sys_failed is None:
            sys_failed = 0
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (datetime.utcnow() -
                            self.start_time).total_seconds()
        message = '%s Stats: elapsed_time=%ds, systems_count=%d,'\
            ' systems_scanned=%d, systems_failed=%d' %\
            (prefix,
             elapsed_time,
             sys_count,
             sys_scanned,
             sys_failed)
        self.log_message(message)

    def log_message(self, message, log_level=logging.INFO):
        """Log a message for this task."""
        actual_message = 'Task %d (%s, %s, %s) - ' % (self.id,
                                                      self.scan_type,
                                                      self.source.source_type,
                                                      self.source.name)
        actual_message += message.strip()
        logger.log(log_level, actual_message)

    @transaction.atomic
    def update_stats(self,
                     description,
                     sys_count=None,
                     sys_scanned=None,
                     sys_failed=None):
        """Update scan task stats.

        :param description: Description to be logged with stats.
        :param sys_count: Total number of systems.
        :param sys_scanned: Systems scanned.
        :param sys_failed: Systems failed during scan.
        """
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

        if stats_changed:
            self.save()
        self._log_stats(description)

    @transaction.atomic
    def increment_stats(self, name,
                        increment_sys_count=False,
                        increment_sys_scanned=False,
                        increment_sys_failed=False):
        """Increment scan task stats.

        Helper method to increment and save values.  Log will be
        produced after stats are updated.
        :param description: Name of entity (host, ip, etc)
        :param increment_sys_count: True if should be incremented.
        :param increment_sys_scanned: True if should be incremented.
        :param increment_sys_failed: True if should be incremented.
        """
        sys_count = None
        sys_failed = None
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

        stat_string = 'PROCESSING %s.' % name
        self.update_stats(stat_string, sys_count=sys_count,
                          sys_scanned=sys_scanned, sys_failed=sys_failed)

    @transaction.atomic
    def start(self):
        """Start a task."""
        self.start_time = datetime.utcnow()
        self.status = ScanTask.RUNNING
        self.status_message = _(messages.ST_STATUS_MSG_RUNNING)
        self.save()
        self.log_current_status()

    @transaction.atomic
    def restart(self):
        """Start a task."""
        self.status = ScanTask.PENDING
        self.status_message = _(messages.ST_STATUS_MSG_RESTARTED)
        self.save()
        self.log_current_status()

    @transaction.atomic
    def pause(self):
        """Pause a task."""
        self.status = ScanTask.PAUSED
        self.status_message = _(messages.ST_STATUS_MSG_PAUSED)
        self.save()
        self.log_current_status()

    @transaction.atomic
    def cancel(self):
        """Cancel a task."""
        self.end_time = datetime.utcnow()
        self.status = ScanTask.CANCELED
        self.status_message = _(messages.ST_STATUS_MSG_CANCELED)
        self.save()
        self.log_current_status()

    @transaction.atomic
    def complete(self, message=None):
        """Complete a task."""
        self.end_time = datetime.utcnow()
        self.status = ScanTask.COMPLETED
        if message:
            self.status_message = message
            self.log_message(self.status_message)
        else:
            self.status_message = _(messages.ST_STATUS_MSG_COMPLETED)
        if self.systems_count is None:
            self.systems_count = 0
        if self.systems_scanned is None:
            self.systems_scanned = 0
        if self.systems_failed is None:
            self.systems_failed = 0
        self.save()
        self._log_stats('COMPLETION STATS.')
        self.log_current_status()

    @transaction.atomic
    def fail(self, message):
        """Fail a task.

        :param message: The error message associated with failure
        """
        self.end_time = datetime.utcnow()
        self.status = ScanTask.FAILED
        self.status_message = message
        self.log_message(self.status_message, log_level=logging.ERROR)
        self.save()
        self._log_stats('FAILURE STATS.')
        self.log_current_status(show_status_message=True,
                                log_level=logging.ERROR)
