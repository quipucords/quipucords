"""Util for common operations."""

import dataclasses
import logging
from datetime import datetime
from json import JSONEncoder
from pathlib import Path

from django.utils.translation import gettext as _
from rest_framework.exceptions import ParseError
from rest_framework.serializers import ValidationError

from compat.pydantic import BaseModel, PydanticErrorProxy

logger = logging.getLogger(__name__)

ALL_IDS_MAGIC_STRING = "all"  # special API input value for not filtering IDs


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


def is_boolean(value):
    """Check if a value is a bool cast as string.

    :param value: The value to check
    :returns: bool indicating if it can be converted
    """
    if isinstance(value, bool):
        return True
    if not isinstance(value, str):
        return False
    return value.lower() in ("true", "false")


def convert_to_boolean(value):
    """Convert a string 'True' or 'False' to boolean.

    :param value: The value to convert
    :return The value as a bool
    """
    if isinstance(value, bool):
        return value
    if is_boolean(value):
        return value.lower() == "true"
    return False


def convert_to_bool_or_none(value):
    """Convert a string "True" or "False" to boolean.

    If value already is a boolean, returns it untouched.
    Otherwise, return None.
    """
    if isinstance(value, bool):
        return value
    if is_boolean(value):
        return value.lower() == "true"
    return None


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
        existing = queryset.filter(name=name).exclude(id=search_id).first()
    if existing is not None:
        error = {"name": [error_message]}
        raise ValidationError(error)


def check_path_validity(path_list):
    """Validate list of paths.

    :param path_list: list of paths to validate
    :return: empty list or list of invalid paths
    """
    invalid_paths = []
    for a_path in path_list:
        if not Path(a_path).is_absolute():
            invalid_paths.append(a_path)
    return invalid_paths


def split_filename(filename) -> tuple[str, str | None]:
    """
    Split a filename into its stem/main name and optional suffix/extension.

    >>> split_filename("hello") == ("hello", None)
    >>> split_filename("hello.txt") == ("hello", "txt")
    >>> split_filename("hello.world.txt") == ("hello.world", "txt")
    """
    path = Path(filename)
    if path.suffix:
        return path.stem, path.suffix[1:]  # remove the leading dot
    else:
        return path.name, None


def expand_scanjob_with_times(scanjob):  # noqa: PLR0912, C901
    """Expand a scanjob object into a JSON dict to send to the user.

    :param scanjob: a ScanJob.

    :returns: a JSON dict with some of the ScanJob's fields.
    """
    # delay import scantask to avoid a circular import issue
    from api.scantask.model import ScanTask

    (
        systems_count,
        systems_scanned,
        systems_failed,
        systems_unreachable,
        system_fingerprint_count,
    ) = scanjob.calculate_counts()
    report_id = scanjob.report_id
    start_time = scanjob.start_time
    end_time = scanjob.end_time
    job_status = scanjob.status
    scan_type = scanjob.scan_type
    job_status_message = scanjob.status_message

    job_json = {
        "id": scanjob.id,
    }

    if report_id is not None:
        job_json["report_id"] = report_id
    if start_time is not None:
        job_json["start_time"] = start_time
    if end_time is not None:
        job_json["end_time"] = end_time
    if systems_count is not None:
        job_json["systems_count"] = systems_count
    if systems_scanned is not None:
        job_json["systems_scanned"] = systems_scanned
    if systems_failed is not None:
        job_json["systems_failed"] = systems_failed
    if systems_unreachable is not None:
        job_json["systems_unreachable"] = systems_unreachable
    if system_fingerprint_count is not None:
        job_json["system_fingerprint_count"] = system_fingerprint_count
    if scan_type is not None:
        job_json["scan_type"] = scan_type
    if job_status_message is not None:
        job_json["status_details"] = {"job_status_message": job_status_message}
    if job_status is not None:
        job_json["status"] = job_status
        if job_status == ScanTask.FAILED:
            failed_tasks = scanjob.tasks.all().order_by("sequence_number")
            status_details = job_json["status_details"]
            for task in failed_tasks:
                task_key = f"task_{task.id}_status_message"
                status_details[task_key] = task.status_message

    return job_json


class RawFactEncoder(JSONEncoder):
    """Customize the JSONField Encoder for RawFact values."""

    def default(self, o):
        """Update the default Encoder to handle types beyond just the basic ones."""
        if isinstance(o, (BaseModel, PydanticErrorProxy)):
            return o.dict()
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, set):
            return sorted(o)
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def set_of_ids_or_all_str(ids) -> set[int] | str:
    """
    Given an input, return a list of integers or the magic "all" string.

    Some of our APIs (e.g. bulk delete) accept a dynamic "ids" argument as a filter.
    This function consolidates the checking and conversion of that dynamic argument.
    This function may raise ParseError if the input is invalid.
    """
    if (
        not isinstance(ids, (list, str))
        or (isinstance(ids, str) and ids != ALL_IDS_MAGIC_STRING)
        or (isinstance(ids, list) and len(ids) == 0)
        or (isinstance(ids, list) and any([not isinstance(_id, int) for _id in ids]))
    ):
        raise ParseError(
            detail=_("Missing 'ids' list of ids or '{token}' string").format(
                token=ALL_IDS_MAGIC_STRING
            )
        )
    elif not isinstance(ids, str):
        ids = set(ids)  # remove duplicates
    return ids
