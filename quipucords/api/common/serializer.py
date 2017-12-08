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
"""Common serializer to remove empty or null values."""

from collections import OrderedDict
from rest_framework.serializers import ModelSerializer


class NotEmptySerializer(ModelSerializer):
    """Serializer for the NotEmptySerializer model.

    Serializer will remove keys with a value of null or None.
    Additionally, it will remove empty lists or empty objects.

    To allow keys to be empty, include
    the 'qpc_allow_empty_fields' attribute in the Meta class.
    For example, to exclude key1 and key2 from
    pruning, add the following to the serializer subclass:

    class Meta:
        qpc_allow_empty_fields = ['key1','key2']
    """

    def __init__(self, *args, **kwargs):
        """Initialize required meta-data."""
        super().__init__(*args, **kwargs)
        meta = getattr(self.__class__, 'Meta', None)
        self.qpc_allow_empty_fields = getattr(
            meta, 'qpc_allow_empty_fields', [])

    def to_representation(self, instance):
        """Override super to remove null or empty values."""
        result = super().to_representation(instance)
        result = OrderedDict([(key, result[key])
                              for key in result
                              if key in self.qpc_allow_empty_fields or
                              isinstance(result[key], (bool, int)) or
                              bool(result[key])])
        return result
