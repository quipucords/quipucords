"""Misc utils for quipucords."""

import json


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
