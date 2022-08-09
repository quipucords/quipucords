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

"""Serializer for system facts models."""

from api.common.serializer import CustomJSONField, NotEmptySerializer
from api.models import DetailsReport

from rest_framework.serializers import CharField, IntegerField, UUIDField


class DetailsReportSerializer(NotEmptySerializer):
    """Serializer for the DetailsReport model."""

    report_type = CharField(read_only=True)
    report_version = CharField(max_length=64, read_only=True)

    sources = CustomJSONField(required=True)
    report_id = IntegerField(read_only=True)
    report_platform_id = UUIDField(format="hex_verbose", read_only=True)
    cached_csv = CharField(required=False, read_only=True)
    cached_masked_csv = CharField(required=False, read_only=True)

    class Meta:
        """Meta class for DetailsReportSerializer."""

        model = DetailsReport
        exclude = ("id", "deployment_report")
