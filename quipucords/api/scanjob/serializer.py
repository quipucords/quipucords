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
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        ValidationError,
                                        ChoiceField,
                                        IntegerField)
from api.models import Source, ScanJob
import api.messages as messages


class SourceField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Source):
            display = 'Source: %s' % instance.name
        return display


class ScanJobSerializer(ModelSerializer):
    """Serializer for the ScanJob model."""

    source = SourceField(queryset=Source.objects.all())
    scan_type = ChoiceField(required=False, choices=ScanJob.SCAN_TYPE_CHOICES)
    status = ChoiceField(required=False, read_only=True,
                         choices=ScanJob.STATUS_CHOICES)
    max_concurrency = IntegerField(required=False, min_value=1, default=50)
    systems_count = IntegerField(required=False, min_value=0, read_only=True)
    systems_scanned = IntegerField(required=False, min_value=0, read_only=True)
    failed_scans = IntegerField(required=False, min_value=0, read_only=True)
    fact_collection_id = IntegerField(read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = '__all__'

    @staticmethod
    def validate_source(source):
        """Make sure the source is present."""
        if not source:
            raise ValidationError(_(messages.SJ_REQ_SOURCE))

        return source
