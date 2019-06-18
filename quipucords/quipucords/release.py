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
"""File to hold release constants."""
import re

BUILD_VERSION = 'BUILD_VERSION_PLACEHOLDER'
DEFAULT_VERSION = '0.0.0'

# pylint: disable=anomalous-backslash-in-string
VERSION_PATTERN = re.compile('\d+\.\d+\.\d+')  # noqa: W605 (invalid-escape-sequence)
if not VERSION_PATTERN.match(BUILD_VERSION):
    BUILD_VERSION = DEFAULT_VERSION
