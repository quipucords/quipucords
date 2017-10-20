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

from django.db import models
from api.scanjob_model import ScanJob


class ResultKeyValue(models.Model):
    """A key value pair of captured data"""
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=1024, null=True)

    def __str__(self):
        return '{ id:%s, key:%s, value:%s }' % (self.id,
                                                self.key,
                                                self.value)

    class Meta:
        verbose_name_plural = 'Result Key Values'


class Results(models.Model):
    """The captured results from a scan"""
    row = models.CharField(max_length=64)
    columns = models.ManyToManyField(ResultKeyValue)

    def __str__(self):
        return '{ id:%s, row:%s, columns:%s }' % (self.id,
                                                  self.row,
                                                  self.columns)

    class Meta:
        verbose_name_plural = 'Results'


class ScanJobResults(models.Model):
    """The results of a scan job"""
    scan_job = models.ForeignKey(ScanJob, on_delete=models.CASCADE)
    results = models.ManyToManyField(Results)
    fact_collection_id = models.IntegerField(null=True)

    def __str__(self):
        return '{ id:%s, scan_job:%s, ' \
            'fact_collection_id:%s, results:%s }' % (self.id,
                                                     self.scan_job,
                                                     self.fact_collection_id,
                                                     self.results)

    class Meta:
        verbose_name_plural = 'Scan Results'
