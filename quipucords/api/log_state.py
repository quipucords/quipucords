# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
"""Store the input log state in the database."""

from django.db import models


class LatestSequenceNumber(models.Model):
    """The latest sequence number."""

    number = models.BigIntegerField()


class DatabaseUUID(models.Model):
    """The UUID of this Sonar installation."""

    uuid = models.UUIDField()
