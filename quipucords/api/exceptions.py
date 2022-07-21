# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Quipucords API exceptions."""

from rest_framework import status
from rest_framework.exceptions import APIException


class FailedDependencyError(APIException):
    """Custom APIException using status code 424."""

    status_code = status.HTTP_424_FAILED_DEPENDENCY
