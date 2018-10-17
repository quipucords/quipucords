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

import api.messages as messages
from api.common.util import is_int
from api.details_report.csv_renderer import (DetailsCSVRenderer)
from api.details_report.util import (create_details_report,
                                     validate_details_report_json)
from api.models import (DetailsReport,
                        ScanJob,
                        ScanTask)
from api.serializers import DetailsReportSerializer

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       renderer_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import (BrowsableAPIRenderer,
                                      JSONRenderer)
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication

from scanner.job import ScanJobRunner

# Get an instance of a logger
# pylint: disable=invalid-name
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'

if authentication_enabled:
    auth_classes = (ExpiringTokenAuthentication,
                    SessionAuthentication)
    perm_classes = (IsAuthenticated,)
else:
    auth_classes = ()
    perm_classes = ()


@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   DetailsCSVRenderer))
def details(request, pk=None):
    """Lookup and return a details system report."""
    if pk is not None:
        if not is_int(pk):
            error = {
                'report_id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
    detail_data = get_object_or_404(DetailsReport.objects.all(), report_id=pk)
    serializer = DetailsReportSerializer(detail_data)
    json_details = serializer.data
    http_accept = request.META.get('HTTP_ACCEPT')
    if http_accept and 'text/csv' not in http_accept:
        json_details.pop('cached_csv', None)
    return Response(json_details)


class DetailsReportsViewSet(mixins.CreateModelMixin,
                            viewsets.GenericViewSet):
    """ModelViewSet to publish system facts."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = DetailsReport.objects.all()
    serializer_class = DetailsReportSerializer

    def create(self, request, *args, **kwargs):
        """Create a details report."""
        # pylint: disable=unused-argument
        # Validate incoming request body
        has_errors, validation_result = validate_details_report_json(
            request.data)
        if has_errors:
            return Response(validation_result,
                            status=status.HTTP_400_BAD_REQUEST)

        # Create FC model and save data
        details_report = create_details_report(request.data)
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
