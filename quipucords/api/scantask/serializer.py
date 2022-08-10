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
"""Module for serializing all model object for database storage."""

from django.utils.translation import gettext as _
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateTimeField,
    IntegerField,
    PrimaryKeyRelatedField,
    ValidationError,
)

from api import messages
from api.common.serializer import NotEmptySerializer
from api.common.util import convert_to_int, is_int
from api.models import ScanTask, Source


class SourceField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_internal_value(self, data):
        """Create internal value."""
        if not is_int(data):
            raise ValidationError(_(messages.SJ_SOURCE_IDS_INV))
        int_data = convert_to_int(data)
        actual_source = Source.objects.filter(id=int_data).first()
        if actual_source is None:
            raise ValidationError(_(messages.SJ_SOURCE_DO_NOT_EXIST % int_data))
        return actual_source

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Source):
            display = "Source: %s" % instance.name
        return display


class ScanTaskSerializer(NotEmptySerializer):
    """Serializer for the ScanTask model."""

    sequence_number = IntegerField(required=False, min_value=0, read_only=True)
    source = SourceField(queryset=Source.objects.all())
    scan_type = ChoiceField(required=False, choices=ScanTask.SCANTASK_TYPE_CHOICES)
    status = ChoiceField(
        required=False, read_only=True, choices=ScanTask.STATUS_CHOICES
    )
    status_message = CharField(required=False)
    systems_count = IntegerField(required=False, min_value=0, read_only=True)
    systems_scanned = IntegerField(required=False, min_value=0, read_only=True)
    systems_failed = IntegerField(required=False, min_value=0, read_only=True)
    systems_unreachable = IntegerField(required=False, min_value=0, read_only=True)
    start_time = DateTimeField(required=False, read_only=True)
    end_time = DateTimeField(required=False, read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanTask
        fields = [
            "sequence_number",
            "source",
            "scan_type",
            "status",
            "status_message",
            "systems_count",
            "systems_scanned",
            "systems_failed",
            "systems_unreachable",
            "start_time",
            "end_time",
        ]

    @staticmethod
    def validate_source(source):
        """Make sure the source is present."""
        if not source:
            raise ValidationError(_(messages.ST_REQ_SOURCE))

        return source
