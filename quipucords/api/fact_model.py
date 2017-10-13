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


class Fact(models.Model):
    """Represents a system fact"""
    etc_release_name = models.CharField(max_length=128, unique=False)
    etc_release_release = models.CharField(max_length=64, unique=False)
    etc_release_version = models.CharField(max_length=64, unique=False)
    connection_uuid = models.UUIDField(unique=False)

    def __str__(self):
        return 'id:{}, etc_release_name:{}, '\
            'etc_release_release:{}, '\
            'etc_release_verison:{}, '\
            'connection_uuid:{}'\
            .format(self.id,
                    self.etc_release_name,
                    self.etc_release_release,
                    self.etc_release_version,
                    self.connection_uuid)


class FactCollection(models.Model):
    """A reported set of facts"""
    facts = models.ManyToManyField(Fact)

    def __str__(self):
        result = '{ id:%s, facts: [' % (self.id)
        for fact in self.facts.values():
            result += '%s, ' % (str(fact))
        result += ']}'
        return result
