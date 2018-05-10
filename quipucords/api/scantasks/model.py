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
import json
import logging
from datetime import datetime

import api.messages as messages
from api.connresults.model import TaskConnectionResult
from api.inspectresults.model import TaskInspectionResult
from api.source.model import Source

from django.db import models, transaction
from django.utils.translation import ugettext as _

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanTask(models.Model):
    """The scan task captures a single source for a scan."""

    # pylint: disable=too-many-instance-attributes
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
    systems_unreachable = models.PositiveIntegerField(null=True)
    sequence_number = models.PositiveIntegerField(null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    connection_result = models.ForeignKey(
        TaskConnectionResult, null=True, on_delete=models.CASCADE)
    inspection_result = models.ForeignKey(
        TaskInspectionResult, null=True, on_delete=models.CASCADE)

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
            'systems_unreachable: {}, '\
            'start_time: {} '\
            'end_time: {}, '\
            'connection_result: {}, '\
            'inspection_result: {}'.format(self.id,
                                           self.scan_type,
                                           self.status,
                                           self.source,
                                           self.sequence_number,
                                           self.systems_count,
                                           self.systems_scanned,
                                           self.systems_failed,
                                           self.systems_unreachable,
                                           self.start_time,
                                           self.end_time,
                                           self.connection_result,
                                           self.inspection_result) + '}'

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
        message = '%s Stats: systems_count=%d,'\
            ' systems_scanned=%d, systems_failed=%d, systems_unreachable=%d' %\
            (prefix,
             sys_count,
             sys_scanned,
             sys_failed,
             sys_unreachable)
        self.log_message(message)

    def log_message(self, message, log_level=logging.INFO):
        """Log a message for this task."""
        elapsed_time = self._compute_elapsed_time()
        actual_message = 'Task %d (%s, %s, %s, elapsed_time: %ds) - ' % \
            (self.id,
             self.scan_type,
             self.source.source_type,
             self.source.name,
             elapsed_time)
        actual_message += message.strip()
        logger.log(log_level, actual_message)

    def _compute_elapsed_time(self):
        """Compute elapsed time."""
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (datetime.utcnow() -
                            self.start_time).total_seconds()
        return elapsed_time

    @transaction.atomic
    def update_stats(self,
                     description,
                     sys_count=None,
                     sys_scanned=None,
                     sys_failed=None,
                     sys_unreachable=None):
        """Update scan task stats.

        :param description: Description to be logged with stats.
        :param sys_count: Total number of systems.
        :param sys_scanned: Systems scanned.
        :param sys_failed: Systems failed during scan.
        :param sys_unreachable: Systems unreachable during scan.
        """
        # pylint: disable=too-many-arguments
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
        if sys_unreachable is not None and \
                sys_unreachable != self.systems_unreachable:
            self.systems_unreachable = sys_unreachable
            stats_changed = True

        if stats_changed:
            self.save()
        self._log_stats(description)

    @transaction.atomic
    def increment_stats(self, name,
                        increment_sys_count=False,
                        increment_sys_scanned=False,
                        increment_sys_failed=False,
                        increment_sys_unreachable=False,
                        prefix='PROCESSING'):
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
        stat_string = '%s %s.' % (prefix, name)
        self.update_stats(stat_string,
                          sys_count=sys_count,
                          sys_scanned=sys_scanned,
                          sys_failed=sys_failed,
                          sys_unreachable=sys_unreachable)

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

        return systems_count,\
            systems_scanned,\
            systems_failed,\
            systems_unreachable

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

    def get_facts(self):
        """Access inspection facts."""
        # pylint: disable=too-many-nested-blocks
        all_systems_facts = []
        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            system_results = self.get_result()
            if system_results:
                # Process all results that were save to db
                for system_result in system_results.systems.all():
                    system_facts = {}
                    for raw_fact in system_result.facts.all():
                        if not raw_fact.value or raw_fact.value == '':
                            continue
                        # Load values as JSON
                        value_to_use = json.loads(raw_fact.value)
                        system_facts[raw_fact.name] = value_to_use
                    if bool(system_facts):
                        all_systems_facts.append(system_facts)

        return all_systems_facts

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
                        if not raw_fact.value or raw_fact.value == '':
                            continue
                        # Load values as JSON
                        value_to_use = json.loads(raw_fact.value)
                        fact[raw_fact.name] = value_to_use

                    if fact.get(identity_key) is None:
                        system_result.facts.all().delete()
                        system_result.delete()

    def get_result(self):
        """Access results from ScanTask.

        Results are expected to be persisted. This method should
        understand how to read persisted results into a dictionary
        using a ScanTask object so others can retrieve them if needed.

        :returns: Scan result object for task (either TaskConnectionResult
        or TaskInspectionResult)
        """
        if self.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            return self.inspection_result
        elif self.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            return self.connection_result
