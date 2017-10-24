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

"""Models system fingerprints."""

from django.db import models
from api.fact.model import FactCollection


class SystemFingerprint(models.Model):
    """Represents system fingerprint"""
    fact_collection_id = models.ForeignKey(FactCollection,
                                           models.CASCADE)
    os_name = models.CharField(max_length=128, unique=False)
    os_release = models.CharField(max_length=64, unique=False)
    os_version = models.CharField(max_length=64, unique=False)

    def __str__(self):
        return '{' + 'id:{}, fact_collection:{}, ' \
            'os_name:{}, os_release:{}, '\
            'os_version:{}' \
            .format(self.id,
                    self.fact_collection_id.id,
                    self.os_name,
                    self.os_release,
                    self.os_version) + '}'
