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
from api.scantasks.model import ScanTask
import api.messages as messages


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan job."""

    max_concurrency = models.PositiveIntegerField(default=50)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'max_concurrency: {}'.format(self.id,
                                           self.max_concurrency) + '}'


class ScanJob(models.Model):
    """The scan job captures all sources and scan tasks for a scan."""

    sources = models.ManyToManyField(Source)
    scan_type = models.CharField(
        max_length=9,
        choices=ScanTask.SCAN_TYPE_CHOICES,
        default=ScanTask.HOST,
    )
    status = models.CharField(
        max_length=20,
        choices=ScanTask.STATUS_CHOICES,
        default=ScanTask.PENDING,
    )
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
