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

import json
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework.serializers import (PrimaryKeyRelatedField,
                                        ValidationError,
                                        IntegerField,
                                        CharField,
                                        DateTimeField)
from api.models import Source, ScanTask, ScanJob, ScanOptions
import api.messages as messages
from api.common.serializer import (NotEmptySerializer,
                                   ValidStringChoiceField,
                                   CustomJSONField)
from api.scantasks.serializer import ScanTaskSerializer
from api.scantasks.serializer import SourceField


class ScanOptionsSerializer(NotEmptySerializer):
    """Serializer for the ScanOptions model."""

    max_concurrency = IntegerField(required=False, min_value=1, default=50)
    disable_optional_products = CustomJSONField(required=False)

    class Meta:
        """Metadata for serializer."""

        model = ScanOptions
        fields = ['max_concurrency',
                  'disable_optional_products']

    # pylint: disable=invalid-name
    @staticmethod
    def validate_disable_optional_products(disable_optional_products):
        """Make sure that extra vars are a dictionary with boolean values."""
        disable_optional_products = ScanJob.get_optional_products(
            disable_optional_products)

        if not isinstance(disable_optional_products, dict):
            raise ValidationError(_(messages.SJ_EXTRA_VARS_DICT))
        for key in disable_optional_products:
            if not isinstance(disable_optional_products[key], bool):
                raise ValidationError(_(messages.SJ_EXTRA_VARS_BOOL))
            elif key not in [ScanJob.JBOSS_EAP,
                             ScanJob.JBOSS_BRMS,
                             ScanJob.JBOSS_FUSE]:
                raise ValidationError(_(messages.SJ_EXTRA_VARS_KEY))
        return json.dumps(disable_optional_products)


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
    status_message = CharField(required=False, max_length=256)
    tasks = TaskField(many=True, read_only=True)
    options = ScanOptionsSerializer(required=False, many=False)
    fact_collection_id = IntegerField(read_only=True)
    start_time = DateTimeField(required=False, read_only=True)
    end_time = DateTimeField(required=False, read_only=True)

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
