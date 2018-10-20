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

import logging
import os

from api.scantask.model import ScanTask

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
    return False


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
    """Validate list of paths.

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
        # pylint: disable=no-else-return
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
        # pylint: disable=too-many-nested-blocks
        headers = set()
        for fact in fact_list:
            fact_addon = {}
            for fact_key in fact.keys():
                if fact_key == 'products':
                    prods = fact.get(fact_key, [])
                    if prods:
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


def expand_scanjob_with_times(scanjob, connect_only=False):
    """Expand a scanjob object into a JSON dict to send to the user.

    :param scanjob: a ScanJob.
    :param connect_only: counts should only include
    connection scan results

    :returns: a JSON dict with some of the ScanJob's fields.
    """
    # pylint: disable=too-many-locals,too-many-branches
    systems_count, \
        systems_scanned, \
        systems_failed, \
        systems_unreachable,\
        system_fingerprint_count = scanjob.calculate_counts(connect_only)
    report_id = scanjob.report_id
    start_time = scanjob.start_time
    end_time = scanjob.end_time
    job_status = scanjob.status
    if not connect_only:
        scan_type = scanjob.scan_type
    job_status_message = scanjob.status_message

    job_json = {
        'id': scanjob.id,
    }

    if report_id is not None:
        job_json['report_id'] = report_id
    if start_time is not None:
        job_json['start_time'] = start_time
    if end_time is not None:
        job_json['end_time'] = end_time
    if systems_count is not None:
        job_json['systems_count'] = systems_count
    if systems_scanned is not None:
        job_json['systems_scanned'] = systems_scanned
    if systems_failed is not None:
        job_json['systems_failed'] = systems_failed
    if systems_unreachable is not None:
        job_json['systems_unreachable'] = systems_unreachable
    if system_fingerprint_count is not None:
        job_json['system_fingerprint_count'] = system_fingerprint_count
    if not connect_only and scan_type is not None:
        job_json['scan_type'] = scan_type
    if job_status_message is not None:
        job_json['status_details'] = {
            'job_status_message': job_status_message}
    if job_status is not None:
        job_json['status'] = job_status
        if job_status == ScanTask.FAILED:
            failed_tasks = scanjob.tasks.all().order_by(
                'sequence_number')
            status_details = job_json['status_details']
            for task in failed_tasks:
                task_key = 'task_%s_status_message' % task.id
                status_details[task_key] = task.status_message

    return job_json
