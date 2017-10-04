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
"""Module for serializing all model object for database storage"""

from django.utils.translation import ugettext as _
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        ValidationError)
from api.networkprofile_model import NetworkProfile
from api.scanjob_model import ScanJob


class NetworkProfileField(PrimaryKeyRelatedField):
    """Representation of the network profile associated with a scan job
    """

    def display_value(self, instance):
        display = instance
        if isinstance(instance, NetworkProfile):
            display = 'NetworkProfile: %s' % instance.name
        return display


class ScanJobSerializer(ModelSerializer):
    """Serializer for the ScanJob model"""

    profile = NetworkProfileField(queryset=NetworkProfile.objects.all())

    class Meta:
        model = ScanJob
        fields = '__all__'

    @staticmethod
    def validate_profile(profile):
        """Make sure the profile is present."""
        if not profile:
            raise ValidationError(_('Scan must have a network profile.'))

        return profile
