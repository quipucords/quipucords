"""Misc utils for quipucords."""

import json
import os
from pathlib import Path


def deep_sort(value):
    """
    Recursively sort a potentially nested object.

    This function only attempts to sort types dict, list, set, and tuple. It does not
    attempt to sort just any Iterable because some also-Iterable types like str should
    never be sorted.

    This function MAY change the types of values to ensure ordered results. For example,
    this function will return a list object when given a set object.
    """
    if isinstance(value, (list, set, tuple)):
        return [deep_sort(item) for item in sorted(value)]
    if not isinstance(value, dict):
        return value
    return {key: deep_sort(value[key]) for key in sorted(value.keys())}


def load_json_from_tarball(json_filename, tarball):
    """Extract a json as dict from given TarFile interface."""
    return json.loads(tarball.extractfile(json_filename).read())


def sanitize_for_utf8_compatibility(value):
    """
    Sanitize the given value of non-UTF-8 bytes.

    Ansible's raw facts may contain unexpected bytes in their `str` representations
    that cannot be encoded as UTF-8. We need to ensure the strings are UTF-8 safe
    before we store them in the database. This means we may lose some bytes from the
    original values, but by using `errors="replace"`, any unexpected bytes will be
    replaced with the `?` character.

    Those original values could be strings, dicts... who knows?! So, we try a few
    different approaches here to cover most cases. We are invoking recursive calls,
    but I expect the objects we sanitize are shallow enough not to be a problem.
    """
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode()
    if isinstance(value, dict):
        return {
            sanitize_for_utf8_compatibility(key): sanitize_for_utf8_compatibility(value)
            for key, value in value.items()
        }
    if isinstance(value, list):
        return [sanitize_for_utf8_compatibility(value) for value in value]
    if isinstance(value, tuple):
        return tuple(sanitize_for_utf8_compatibility(value) for value in value)
    return value


def is_valid_cache_file(file_path: str | None) -> bool:
    """Check if a file exists, has non-zero size, and is both readable and writable."""
    if not file_path:
        return False
    path = Path(file_path).absolute()
    return (
        path.exists()
        and path.is_file()
        and path.stat().st_size > 0
        and os.access(file_path, os.R_OK)
        and os.access(file_path, os.W_OK)
    )
