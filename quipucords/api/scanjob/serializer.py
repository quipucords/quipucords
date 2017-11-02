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
from api.models import NetworkProfile, ScanJob
import api.messages as messages


class NetworkProfileField(PrimaryKeyRelatedField):
    """Representation of the network profile associated with a scan job."""

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, NetworkProfile):
            display = 'NetworkProfile: %s' % instance.name
        return display


class ScanJobSerializer(ModelSerializer):
    """Serializer for the ScanJob model."""

    profile = NetworkProfileField(queryset=NetworkProfile.objects.all())
    scan_type = ChoiceField(required=False, choices=ScanJob.SCAN_TYPE_CHOICES)
    status = ChoiceField(required=False, read_only=True,
                         choices=ScanJob.STATUS_CHOICES)
    max_concurrency = IntegerField(required=False, min_value=1, default=50)
    systems_count = IntegerField(required=False, min_value=0, read_only=True)
    systems_scanned = IntegerField(required=False, min_value=0, read_only=True)
    fact_collection_id = IntegerField(read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = '__all__'

    @staticmethod
    def validate_profile(profile):
        """Make sure the profile is present."""
        if not profile:
            raise ValidationError(_(messages.SJ_REQ_PROFILE))

        return profile
