"""Infer release version."""

import re
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from warnings import warn

VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")


@lru_cache
def infer_version():
    """Infer release version."""
    fallback_version = "0.0.0"
    try:
        package_version = version("quipucords")
    except PackageNotFoundError:
        warn("Package 'quipucords' can't be found. Is it installed?")
        return fallback_version

    if not package_version or not VERSION_PATTERN.match(package_version):
        package_version = fallback_version
    return package_version
