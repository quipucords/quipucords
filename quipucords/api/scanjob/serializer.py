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

from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework.serializers import (PrimaryKeyRelatedField,
                                        ValidationError,
                                        IntegerField,
                                        JSONField)
from api.models import Source, ScanTask, ScanJob, ScanOptions
import api.messages as messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.scantasks.serializer import ScanTaskSerializer
from api.scantasks.serializer import SourceField


class ScanOptionsSerializer(NotEmptySerializer):
    """Serializer for the ScanOptions model."""

    max_concurrency = IntegerField(required=False, min_value=1, default=50)
    optional_products = JSONField(required=False)

    class Meta:
        """Metadata for serializer."""

        model = ScanOptions
        fields = ['max_concurrency',
                  'optional_products']


class TaskField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_representation(self, value):
        """Create output representation."""
        serializer = ScanTaskSerializer(value)
        return serializer.data


class ScanJobSerializer(NotEmptySerializer):
    """Serializer for the ScanJob model."""

    sources = SourceField(many=True, queryset=Source.objects.all())
    scan_type = ValidStringChoiceField(required=False,
                                       choices=ScanTask.SCAN_TYPE_CHOICES)
    status = ValidStringChoiceField(required=False, read_only=True,
                                    choices=ScanTask.STATUS_CHOICES)
    tasks = TaskField(many=True, read_only=True)
    options = ScanOptionsSerializer(required=False, many=False)
    fact_collection_id = IntegerField(read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        """Create a scan job."""
        options = validated_data.pop('options', None)
        scanjob = super().create(validated_data)
        if options:
            options = ScanOptions.objects.create(**options)
        else:
            options = ScanOptions()
        options.save()
        scanjob.options = options
        scanjob.save()

        return scanjob

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources
