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

import api.messages as messages
from api.scantask.model import ScanTask

from django.utils.translation import gettext as _

from rest_framework.serializers import ValidationError


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def is_int(value):
    """Check if a value is convertable to int.

    :param value: The value to convert
    :returns: bool indicating if it can be converted
    """
    if isinstance(value, int):
        return True
    if isinstance(value, bool):
        return False
    if not isinstance(value, str):
        return False

    try:
        int(value)
        return True
    except ValueError:
        return False


def convert_to_int(value):
    """Convert value to int if possible.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if not is_int(value):
        return None
    return int(value)


def is_float(value):
    """Check if a value is convertable to float.

    :param value: The value to convert
    :returns: bool indicating if it can be converted
    """
    if isinstance(value, float):
        return True
    if isinstance(value, int):
        return False
    if not isinstance(value, str):
        return False

    try:
        float(value)
        return True
    except ValueError:
        return False


def convert_to_float(value):
    """Convert value to float if possible.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if not is_float(value):
        return None
    return float(value)


def is_boolean(value):
    """Check if a value is a bool cast as string.

    :param value: The value to check
    :returns: bool indicating if it can be converted
    """
    if isinstance(value, bool):
        return True
    if not isinstance(value, str):
        return False
    return value.lower() in ('true', 'false')


def convert_to_boolean(value):
    """Convert a string 'True' or 'False' to boolean.

    :param value: The value to convert
    :return The value as a bool
    """
    if isinstance(value, bool):
        return value
    if is_boolean(value):
        return value.lower() == 'true'
    return False


def validate_query_param_bool(param, param_name='mask'):
    """Validate that the query param is a boolean return the bool.

    :param: param: The query param to evaluate
    :param name: <str> The name of the param
    :return The value as a boolean or a validation error
    """
    if is_boolean(param):
        return convert_to_boolean(param)
    error = {
        param_name: [_(
            messages.QUERY_PARAM_INVALID %
            (param_name, [True, False, 'true', 'false', 'True', 'False']))]
    }
    raise ValidationError(error)


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


def mask_data_general(report, mac_and_ip_facts, name_related_facts):
    """Mask the data that is given and return it.

    :param report: <dict> the report to mask
    :param mac_and_ip_facts: <list> a list of mac/ip related facts
    :param name_related_facts: <list> a list of name related facts

    :returns: <dict> the report with sensitive info masked.
    """
    for system in report:
        for address_list in mac_and_ip_facts:
            new_addrs = []
            addrs_to_mask = system.get(address_list)
            if addrs_to_mask:
                for addr in addrs_to_mask:
                    new_addrs.append(str(hash(addr)))
                system[address_list] = new_addrs
        for name in name_related_facts:
            name_to_change = system.get(name)
            if name_to_change:
                system[name] = str(hash(name_to_change))
    return report
