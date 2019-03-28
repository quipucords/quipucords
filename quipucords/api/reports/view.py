#
# Copyright (c) 2018-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""View for reports."""

import logging
import os

import api.messages as messages
from api.common.util import is_int
from api.deployments_report.view import (build_cached_json_report,
                                         validate_filters)
from api.insights_report.view import build_cached_insights_json_report
from api.models import DeploymentsReport, DetailsReport
from api.reports.reports_gzip_renderer import (ReportsGzipRenderer)
from api.serializers import DetailsReportSerializer

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.authentication import (SessionAuthentication,
                                           TokenAuthentication)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       renderer_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError


# Get an instance of a logger
# pylint: disable=invalid-name
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'

if authentication_enabled:
    auth_classes = (TokenAuthentication,
                    SessionAuthentication)
    perm_classes = (IsAuthenticated,)
else:
    auth_classes = ()
    perm_classes = ()


@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((ReportsGzipRenderer,))
def reports(request, pk=None):
    """Lookup and return reports."""
    reports_dict = dict()
    if pk is not None:
        if not is_int(pk):
            error = {
                'report_id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
    reports_dict['report_id'] = pk
    # details
    details_data = get_object_or_404(DetailsReport.objects.all(), report_id=pk)
    serializer = DetailsReportSerializer(details_data)
    json_details = serializer.data
    json_details.pop('cached_csv', None)
    reports_dict['details_json'] = json_details
    # deployments
    validate_filters(request.query_params)
    deployments_data = get_object_or_404(DeploymentsReport.objects.all(),
                                         report_id=pk)
    if deployments_data.status != DeploymentsReport.STATUS_COMPLETE:
        deployments_id = deployments_data.details_report.id
        return Response({'detail':
                         'Deployment report %s could not be created.'
                         '  See server logs.' % deployments_id},
                        status=status.HTTP_424_FAILED_DEPENDENCY)
    reports_dict['deployments_json'] = \
        build_cached_json_report(deployments_data)
    # insights
    insights_report = build_cached_insights_json_report(deployments_data)
    if not insights_report.get('detail'):
        reports_dict['insights_json'] = insights_report
    else:
        logger.warning('Insights report %s could not be created.',
                       deployments_data.details_report.id)
    return Response(reports_dict)
