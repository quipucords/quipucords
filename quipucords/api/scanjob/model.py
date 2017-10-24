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
from api.networkprofile.model import NetworkProfile


class ScanJob(models.Model):
    """The host credential for connecting to host systems via ssh"""
    DISCOVERY = 'discovery'
    HOST = 'host'
    SCAN_TYPE_CHOICES = ((HOST, HOST), (DISCOVERY, DISCOVERY))

    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    CANCELED = 'canceled'
    COMPLETED = 'completed'
    FAILED = 'failed'
    STATUS_CHOICES = ((PENDING, PENDING), (RUNNING, RUNNING), (PAUSED, PAUSED),
                      (COMPLETED, COMPLETED), (CANCELED, CANCELED),
                      (FAILED, FAILED))

    profile = models.ForeignKey(NetworkProfile, on_delete=models.CASCADE)
    scan_type = models.CharField(
        max_length=9,
        choices=SCAN_TYPE_CHOICES,
        default=HOST,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )

    def __str__(self):
        return '{id:%s, scan_type:%s, profile:%s}' % (self.id,
                                                      self.scan_type,
                                                      self.profile)

    class Meta:
        verbose_name_plural = 'Scan Jobs'
