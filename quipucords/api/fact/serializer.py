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

"""Serializer for system facts models."""

from rest_framework.serializers import ChoiceField, JSONField
from api.models import FactCollection
from api.common.serializer import NotEmptySerializer


class FactCollectionSerializer(NotEmptySerializer):
    """Serializer for the FactCollection model."""

    status = ChoiceField(
        choices=FactCollection.FC_STATUS_CHOICES,
        read_only=True)
    sources = JSONField(required=False)

    class Meta:
        """Meta class for FactCollectionSerializer."""

        model = FactCollection
        fields = ['id', 'status', 'sources']

    @staticmethod
    def validate_sources(sources):
        """Validate sources field."""
        # FIXME add code to validate sources
        print('hereS')
        print(sources)
        return sources
