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
from django.utils.translation import ugettext as _
from django.db import models
from api.source.model import Source
import api.messages as messages


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
    prerequisites = models.ManyToManyField('ScanTask')
    systems_count = models.PositiveIntegerField(null=True)
    systems_scanned = models.PositiveIntegerField(null=True)
    systems_failed = models.PositiveIntegerField(null=True)
    sequence_number = models.PositiveIntegerField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'scan_type:{}, '\
            'status:{}, '\
            'source:{}, '\
            'sequence_number:{}, '\
            'systems_count: {}, '\
            'systems_scanned: {}, '\
            'systems_failed: {}, '.format(self.id,
                                          self.scan_type,
                                          self.status,
                                          self.source,
                                          self.sequence_number,
                                          self.systems_count,
                                          self.systems_scanned,
                                          self.systems_failed) + '}'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_TASKS_MSG)
