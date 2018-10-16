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

"""Viewset for system facts models."""

import logging
import os

from api.fact.util import (create_fact_collection,
                           validate_fact_collection_json)
from api.models import (DetailsReport,
                        ScanJob,
                        ScanTask)
from api.serializers import FactCollectionSerializer

from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication

from scanner.job import ScanJobRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-many-ancestors


class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """ModelViewSet to publish system facts."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = DetailsReport.objects.all()
    serializer_class = FactCollectionSerializer

    def create(self, request, *args, **kwargs):
        """Create a details report."""
        # pylint: disable=unused-argument
        # Validate incoming request body
        has_errors, validation_result = validate_fact_collection_json(
            request.data)
        if has_errors:
            return Response(validation_result,
                            status=status.HTTP_400_BAD_REQUEST)

        # Create FC model and save data
        details_report = create_fact_collection(request.data)
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                           details_report=details_report)
        scan_job.save()
        scan_job.queue()
        runner = ScanJobRunner(scan_job)
        runner.run()

        if scan_job.status != ScanTask.COMPLETED:
            # pylint: disable=no-member
            error_json = {
                'error': scan_job.tasks.first().status_message
            }
            return Response(error_json,
                            status=status.HTTP_400_BAD_REQUEST)

        scan_job = ScanJob.objects.get(pk=scan_job.id)
        details_report = DetailsReport.objects.get(pk=details_report.id)

        # Prepare REST response body
        serializer = self.get_serializer(details_report)
        result = serializer.data
        return Response(result, status=status.HTTP_201_CREATED)
