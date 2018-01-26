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

These models are used in the REST definitions
"""

from django.utils.translation import ugettext as _
from django.db import models
from api.scantasks.model import ScanTask
from api.source.model import Source
import api.messages as messages


class RawFact(models.Model):
    """A model of a raw fact."""

    name = models.CharField(max_length=1024)
    value = models.TextField()

    def __str__(self):
        """Convert to string."""
        return '{ id:%s, name:%s, value:%s }' % \
            (self.id, self.name, self.value)

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_KEY_VALUES_MSG)


class SystemInspectionResult(models.Model):
    """A model the of captured system data."""

    SUCCESS = 'success'
    FAILED = 'failed'
    UNREACHABLE = 'unreachable'
    CONN_STATUS_CHOICES = ((SUCCESS, SUCCESS), (FAILED, FAILED),
                           (UNREACHABLE, UNREACHABLE))

    name = models.CharField(max_length=1024)
    status = models.CharField(max_length=12, choices=CONN_STATUS_CHOICES)
    facts = models.ManyToManyField(RawFact)

    def __str__(self):
        """Convert to string."""
        return '{ id:%s, name:%s, status:%s, facts:%s }' % \
            (self.id, self.name, self.status, self.facts)

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_KEY_VALUES_MSG)


class InspectionResult(models.Model):
    """The captured connection results from a scan."""

    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    scan_task = models.ForeignKey(ScanTask, on_delete=models.CASCADE)
    systems = models.ManyToManyField(SystemInspectionResult)

    def __str__(self):
        """Convert to string."""
        return '{ ' + 'id:{}, '\
            'source:{}, '\
            'scan_job:{}, '\
            'systems:{}'\
            .format(self.id,
                    self.source,
                    self.scan_task,
                    self.systems) + ' }'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_RESULTS_MSG)


class InspectionResults(models.Model):
    """The results of a connection scan."""

    scan_job = models.ForeignKey('ScanJob', on_delete=models.CASCADE)
    results = models.ManyToManyField(InspectionResult)

    def __str__(self):
        """Convert to string."""
        return '{ id:%s }' % (self.id)

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_RESULTS_MSG)
