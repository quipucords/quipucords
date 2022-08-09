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
"""Common serializer to remove empty or null values."""

import json
from collections import OrderedDict

from rest_framework.serializers import (
    ChoiceField,
    Field,
    ListSerializer,
    ModelSerializer,
    ValidationError,
)

from api import messages


class ValidStringChoiceField(ChoiceField):
    """Updated handling for choice field."""

    def to_internal_value(self, data):
        """Create internal value."""
        valid_values = self.choices.keys()
        values_str = ",".join(valid_values)
        if not isinstance(data, str):
            raise ValidationError(messages.COMMON_CHOICE_STR % (values_str))
        if data == "":
            raise ValidationError(messages.COMMON_CHOICE_BLANK % (values_str))
        if data not in valid_values:
            raise ValidationError(messages.COMMON_CHOICE_INV % (data, values_str))
        return data


class NotEmptyMixin:
    """Mixin to remove null values from Serialized data.

    Serializers created with this mixin will remove keys with a
    value of null or None. Additionally, it will remove empty
    lists or empty objects.

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
        meta = getattr(self.__class__, "Meta", None)
        self.qpc_allow_empty_fields = getattr(meta, "qpc_allow_empty_fields", [])

    def to_representation(self, instance):
        """Override super to remove null or empty values."""
        result = super().to_representation(instance)
        result = OrderedDict(
            [
                (key, result[key])
                for key in result
                if key in self.qpc_allow_empty_fields
                or isinstance(result[key], (bool, int))
                or bool(result[key])
            ]
        )
        return result


class NotEmptySerializer(NotEmptyMixin, ModelSerializer):
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


class CustomJSONField(Field):
    """Serializer reading and writing JSON to CharField."""

    def to_internal_value(self, data):
        """Transform  python object to JSON str."""
        return json.dumps(data)

    def to_representation(self, value):
        """Transform JSON str to python object."""
        if value == "":
            return value
        return json.loads(value)


class ForcedListSerializer(ListSerializer):  # pylint: disable=abstract-method
    """Serializer that forces data output as list."""

    def to_representation(self, data):
        """Force instance as list."""
        if not isinstance(data, list):
            data = [data]
        return super().to_representation(data)
