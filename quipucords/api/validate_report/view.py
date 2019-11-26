#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""View for validating & creating report hashes."""
import hashlib
import logging
import os

from api.user.authentication import QuipucordsExpiringTokenAuthentication

from rest_framework import status
from rest_framework.authentication import (SessionAuthentication)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# pylint: disable=invalid-name
# Get an instance of a logger
logger = logging.getLogger(__name__)
authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'

if authentication_enabled:
    auth_classes = (QuipucordsExpiringTokenAuthentication,
                    SessionAuthentication)
    perm_classes = (IsAuthenticated,)
else:
    auth_classes = ()
    perm_classes = ()


def create_hash(report_data):
    """Create a report hash."""
    sha_signature = \
        hashlib.sha256(str(report_data).encode()).hexdigest()
    return sha_signature


@api_view(['PUT'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def validate_hash(request):
    """Validate a report hash."""
    report = request.data.get('report')
    test_hash = request.data.get('hash')
    if report is None or test_hash is None:
        return Response({'detail':
                         'A report and hash must be provided to validate.'},
                        status=status.HTTP_424_FAILED_DEPENDENCY)
    actual_hash = create_hash(report)
    hash_matches = False
    if actual_hash == test_hash:
        hash_matches = True
    return Response(hash_matches, status=status.HTTP_200_OK)
