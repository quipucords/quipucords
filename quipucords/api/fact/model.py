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

"""Models to capture system facts."""

from django.db import models


class SystemFacts(models.Model):
    """Represents a system fact."""

    connection_host = models.CharField(
        max_length=256, unique=False, blank=True, null=True)
    connection_port = models.PositiveIntegerField(unique=False, null=True)
    connection_uuid = models.UUIDField(unique=False)
    cpu_count = models.PositiveIntegerField(unique=False, null=True)
    cpu_core_per_socket = models.PositiveIntegerField(unique=False, null=True)
    cpu_siblings = models.PositiveIntegerField(unique=False, null=True)
    cpu_hyperthreading = models.NullBooleanField()
    cpu_socket_count = models.PositiveIntegerField(unique=False, null=True)
    cpu_core_count = models.PositiveIntegerField(unique=False, null=True)
    date_anaconda_log = models.DateField(null=True)
    date_yum_history = models.DateField(null=True)
    etc_release_name = models.CharField(max_length=64, unique=False)
    etc_release_version = models.CharField(max_length=64, unique=False)
    etc_release_release = models.CharField(max_length=128, unique=False)
    virt_virt = models.CharField(max_length=64, unique=False, null=True)
    virt_type = models.CharField(max_length=64, unique=False, null=True)
    virt_num_guests = models.PositiveIntegerField(unique=False, null=True)
    virt_num_running_guests = models.PositiveIntegerField(
        unique=False, null=True)
    virt_what_type = models.CharField(max_length=64, unique=False, null=True)

    def __str__(self):
        """Convert to string."""
        return 'id:{}, '\
            'connection_host:{}'\
            'connection_port:{}'\
            'connection_uuid:{}'\
            'cpu_count:{}'\
            'cpu_core_per_socket:{}'\
            'cpu_siblings:{}'\
            'cpu_hyperthreading:{}'\
            'cpu_socket_count:{}'\
            'cpu_core_count:{}'\
            'date_anaconda_log:{}'\
            'date_yum_history:{}'\
            'etc_release_name:{}, '\
            'etc_release_version:{}, '\
            'etc_release_release:{}, '\
            'virt_virt:{}'\
            'virt_type:{}'\
            'virt_num_guests:{}'\
            'virt_num_running_guests:{}'\
            'virt_what_type:{}'\
            .format(self.id,
                    self.connection_host,
                    self.connection_port,
                    self.connection_uuid,
                    self.cpu_count,
                    self.cpu_core_per_socket,
                    self.cpu_siblings,
                    self.cpu_hyperthreading,
                    self.cpu_socket_count,
                    self.cpu_core_count,
                    self.date_anaconda_log,
                    self.date_yum_history,
                    self.etc_release_name,
                    self.etc_release_version,
                    self.etc_release_release,
                    self.virt_virt,
                    self.virt_type,
                    self.virt_num_guests,
                    self.virt_num_running_guests,
                    self.virt_what_type)


class FactCollection(models.Model):
    """A reported set of facts."""

    facts = models.ManyToManyField(SystemFacts)

    def __str__(self):
        """Convert to string."""
        result = '{ id:%s, facts: [' % (self.id)
        for fact in self.facts.values():
            result += '%s, ' % (str(fact))
        result += ']}'
        return result
