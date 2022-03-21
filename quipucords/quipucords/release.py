#
# Copyright 2019 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
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
