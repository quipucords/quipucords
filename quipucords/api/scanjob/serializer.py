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
                                        IntegerField,
                                        CharField,
                                        DateTimeField)
from api.models import (Scan,
                        ScanTask,
                        ScanJob,
                        ScanJobOptions)
import api.messages as messages
from api.common.serializer import (NotEmptySerializer,
                                   ValidStringChoiceField,
                                   CustomJSONField)
from api.scantasks.serializer import ScanTaskSerializer
from api.scantasks.serializer import SourceField
from api.common.util import is_int, convert_to_int


class ScanJobOptionsSerializer(NotEmptySerializer):
    """Serializer for the ScanJobOptions model."""

    max_concurrency = IntegerField(read_only=True)
    disable_optional_products = CustomJSONField(read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJobOptions
        fields = ['max_concurrency',
                  'disable_optional_products']


class ScanField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_internal_value(self, data):
        """Create internal value."""
        if not is_int(data):
            raise ValidationError(_(messages.SJ_SCAN_IDS_INV))
        int_data = convert_to_int(data)
        actual_scan = Scan.objects.filter(id=int_data).first()
        if actual_scan is None:
            raise ValidationError(
                _(messages.SJ_SCAN_DO_NOT_EXIST % int_data))
        return actual_scan

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Scan):
            display = 'Scan: %s' % instance.name
        return display


class TaskField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_representation(self, value):
        """Create output representation."""
        serializer = ScanTaskSerializer(value)
        return serializer.data


class ScanJobSerializer(NotEmptySerializer):
    """Serializer for the ScanJob model."""

    scan = ScanField(required=True, many=False, queryset=Scan.objects.all())
    sources = SourceField(many=True, read_only=True)
    scan_type = ValidStringChoiceField(read_only=True,
                                       choices=ScanTask.SCAN_TYPE_CHOICES)
    status = ValidStringChoiceField(read_only=True,
                                    choices=ScanTask.STATUS_CHOICES)
    status_message = CharField(read_only=True)
    tasks = TaskField(many=True, read_only=True)
    options = ScanJobOptionsSerializer(read_only=True, many=False)
    fact_collection_id = IntegerField(read_only=True)
    start_time = DateTimeField(required=False, read_only=True)
    end_time = DateTimeField(required=False, read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = ['id',
                  'scan',
                  'sources',
                  'scan_type',
                  'status',
                  'status_message',
                  'tasks',
                  'options',
                  'fact_collection_id',
                  'start_time',
                  'end_time']

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources
