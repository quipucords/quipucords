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
from api.common.serializer import (CustomJSONField,
                                   NotEmptySerializer)
from api.models import FactCollection

from rest_framework.serializers import (CharField,
                                        ChoiceField)


class FactCollectionSerializer(NotEmptySerializer):
    """Serializer for the FactCollection model."""

    sources = CustomJSONField(required=True)
    csv_content = CharField(required=False, read_only=True)
    status = ChoiceField(
        read_only=True, choices=FactCollection.FC_STATUS_CHOICES)

    class Meta:
        """Meta class for FactCollectionSerializer."""

        model = FactCollection
        fields = '__all__'
