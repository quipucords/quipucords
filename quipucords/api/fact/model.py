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


class FactCollection(models.Model):
    """A reported set of facts."""

    FC_STATUS_PERSISTED = 'persisted'
    FC_STATUS_COMPLETE = 'complete'
    FC_STATUS_CHOICES = ((FC_STATUS_PERSISTED,
                          FC_STATUS_PERSISTED),
                         (FC_STATUS_COMPLETE,
                          FC_STATUS_COMPLETE))

    status = models.CharField(
        max_length=16,
        choices=FC_STATUS_CHOICES,
        default=FC_STATUS_PERSISTED
    )
    path = models.CharField(max_length=256)

    def __str__(self):
        """Convert to string."""
        return '{' +\
            'id:{}, status:{}, path:{}'.format(self.id,
                                               self.status,
                                               self.path) + '}'
