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

"""Util for common operations."""

import os
import logging
from rest_framework.serializers import ValidationError


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def is_int(value):
    """Check if a value is convertable to int.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if isinstance(value, int):
        return True

    try:
        int(value)
        return True
    except ValueError:
        return False


def convert_to_int(value):
    """Convert value to in if possible.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if not is_int(value):
        return None
    return int(value)


def is_boolean(value):
    """Check if a value is a bool cast as string.

    :param value: The value to check
    :returns True if it is a bool, False if not
    """
    return value.lower() in ('true', 'false')


def convert_to_boolean(value):
    """Convert a string 'True' or 'False' to boolean.

    :param value: The value to convert
    :return The value as a bool
    """
    if is_boolean(value):
        return value.lower() == 'true'


def check_for_existing_name(queryset, name, error_message, search_id=None):
    """Look for existing (different object) with same name.

    :param queryset: Queryset used in searches
    :param name: Name of scan to look for
    :param error_message: message to display
    :param search_id: ID to exclude from search for existing
    """
    if search_id is None:
        # Look for existing with same name (create)
        existing = queryset.filter(name=name).first()
    else:
        # Look for existing.  Same name, different id (update)
        existing = queryset.filter(
            name=name).exclude(id=search_id).first()
    if existing is not None:
        error = {
            'name': [error_message]
        }
        raise ValidationError(error)

def check_path_validity(path_list):
    """Given a list of paths it verifies that all paths are valid absolute
    path inputs for a scoped scan. If not it return a list of invalid paths.
    :param path_list: list of paths to validate
    :return: empty list or list of invalid paths
    """
    invalid_paths = []
    for a_path in path_list:
        if not os.path.isabs(a_path):
            invalid_paths.append(a_path)
    return invalid_paths

class CSVHelper:
    """Helper for CSV serialization of list/dict values."""

    ANSIBLE_ERROR_MESSAGE = 'Error. See logs.'

    def serialize_value(self, header, fact_value):
        """Serialize a fact value to a CSV value."""
        if isinstance(fact_value, dict):
            return self.serialize_dict(header, fact_value)
        elif isinstance(fact_value, list):
            return self.serialize_list(header, fact_value)
        return fact_value

    def serialize_list(self, header, fact_list):
        """Serialize a list to a CSV value."""
        # Return empty string for empty list
        if not bool(fact_list):
            return ''

        result = '['
        value_string = '%s;'
        for item in fact_list:
            if isinstance(item, list):
                result += value_string % self.serialize_list(header, item)
            elif isinstance(item, dict):
                result += value_string % self.serialize_dict(header, item)
            else:
                result += value_string % item
        result = result[:-1] + ']'
        return result

    def serialize_dict(self, header, fact_dict):
        """Serialize a dict to a CSV value."""
        # Return empty string for empty dict
        if not bool(fact_dict):
            return ''
        if fact_dict.get('rc') is not None:
            logger.error(
                'Fact appears to be raw ansible output. %s=%s',
                header, fact_dict)
            return self.ANSIBLE_ERROR_MESSAGE

        result = '{'
        value_string = '%s:%s;'
        for key, value in fact_dict.items():
            if isinstance(value, list):
                result += value_string % (key,
                                          self.serialize_list(header, value))
            elif isinstance(value, dict):
                result += value_string % (key,
                                          self.serialize_dict(header, value))
            else:
                result += value_string % (key, value)
        result = result[:-1] + '}'
        return result

    @staticmethod
    def generate_headers(fact_list, exclude=None):
        """Generate column headers from fact list."""
        headers = set()
        for fact in fact_list:
            fact_addon = {}
            for fact_key in fact.keys():
                if fact_key == 'products':
                    prods = fact.get(fact_key, [])
                    for prod in prods:
                        prod_name = prod.get('name')
                        if prod_name:
                            prod_name = prod_name.lower()
                            headers.add(prod_name)
                            fact_addon[prod_name] = prod.get('presence',
                                                             'unknown')
                else:
                    headers.add(fact_key)
            fact.update(fact_addon)

        if exclude and isinstance(exclude, set):
            headers = headers - exclude
        return sorted(list(headers))
