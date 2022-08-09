#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Models to capture system facts."""

import json
import uuid

from django.db import models

from api.common.common_report import REPORT_TYPE_CHOICES, REPORT_TYPE_DETAILS


class DetailsReport(models.Model):
    """A reported set of facts."""

    report_type = models.CharField(
        max_length=11, choices=REPORT_TYPE_CHOICES, default=REPORT_TYPE_DETAILS
    )
    report_version = models.CharField(max_length=64, null=False)
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    sources = models.TextField(null=False)
    report_id = models.IntegerField(null=True)
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="details_report", null=True
    )
    cached_csv = models.TextField(null=True)
    cached_masked_csv = models.TextField(null=True)

    def __str__(self):
        """Convert to string."""
        return (
            "{" + '"id":{}, '
            '"report_type":"details", '
            '"sources":{}'.format(self.id, self.sources) + "}"
        )

    def get_sources(self):
        """Access facts as python dict instead of str.

        :returns: facts as a python dict
        """
        return json.loads(self.sources)
