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


class Credential(models.Model):
    """The base credential model, all of which will have a name"""
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Credentials'


class HostCredential(Credential):
    """The host credential for connecting to host systems via ssh"""
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    sudo_password = models.CharField(max_length=128)
    ssh_keyfile = models.CharField(max_length=1024)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Host Credentials'
