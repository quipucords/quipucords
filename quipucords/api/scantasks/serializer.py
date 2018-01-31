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

from django.utils.translation import ugettext as _
from rest_framework.serializers import (PrimaryKeyRelatedField,
                                        ValidationError,
                                        ChoiceField,
                                        IntegerField,
                                        CharField,
                                        TimeField)
from api.models import Source, ScanTask
import api.messages as messages
from api.common.serializer import NotEmptySerializer
from api.common.util import is_int, convert_to_int


class SourceField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_internal_value(self, data):
        """Create internal value."""
        if not is_int(data):
            raise ValidationError(_(messages.SJ_SOURCE_IDS_INV))
        int_data = convert_to_int(data)
        actual_source = Source.objects.filter(id=int_data).first()
        if actual_source is None:
            raise ValidationError(
                _(messages.SJ_SOURCE_DO_NOT_EXIST % int_data))
        return actual_source

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Source):
            display = 'Source: %s' % instance.name
        return display


class ScanTaskSerializer(NotEmptySerializer):
    """Serializer for the ScanTask model."""

    source = SourceField(queryset=Source.objects.all())
    scan_type = ChoiceField(required=False, choices=ScanTask.SCAN_TYPE_CHOICES)
    status = ChoiceField(required=False, read_only=True,
                         choices=ScanTask.STATUS_CHOICES)
    status_message = CharField(required=False, max_length=256)
    systems_count = IntegerField(required=False, min_value=0, read_only=True)
    systems_scanned = IntegerField(required=False, min_value=0, read_only=True)
    systems_failed = IntegerField(required=False, min_value=0, read_only=True)
    start_time = TimeField(required=False)
    end_time = TimeField(required=False)

    class Meta:
        """Metadata for serializer."""

        model = ScanTask
        fields = ['source', 'scan_type', 'status', 'status_message',
                  'systems_count', 'systems_scanned',
                  'systems_failed', 'start_time', 'end_time']

    @staticmethod
    def validate_source(source):
        """Make sure the source is present."""
        if not source:
            raise ValidationError(_(messages.ST_REQ_SOURCE))

        return source
