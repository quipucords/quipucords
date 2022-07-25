#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""View for system reports."""
import json
import logging
import os

import api.messages as messages
from api.common.report_json_gzip_renderer import (ReportJsonGzipRenderer)
from api.common.util import is_int, validate_query_param_bool
from api.deployments_report.csv_renderer import (DeploymentCSVRenderer)
from api.models import (DeploymentsReport)
from api.user.authentication import QuipucordsExpiringTokenAuthentication

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.authentication import (SessionAuthentication)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       renderer_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import (BrowsableAPIRenderer,
                                      JSONRenderer)
from rest_framework.response import Response
from rest_framework.serializers import ValidationError


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


# pylint: disable=inconsistent-return-statements
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   DeploymentCSVRenderer, ReportJsonGzipRenderer))
def deployments(request, pk=None):
    """Lookup and return a deployment system report."""
    if not is_int(pk):
        error = {
            'report_id': [_(messages.COMMON_ID_INV)]
        }
        raise ValidationError(error)
    mask_report = request.query_params.get('mask', False)
    report = get_object_or_404(DeploymentsReport.objects.all(), report_id=pk)
    if report.status != DeploymentsReport.STATUS_COMPLETE:
        return Response({'detail':
                         'Deployment report %s could not be created.'
                         '  See server logs.' % report.details_report.id},
                        status=status.HTTP_424_FAILED_DEPENDENCY)
    deployments_report = build_cached_json_report(report, mask_report)
    if deployments_report:
        return Response(deployments_report)
    error = {'detail':
             'Deployments report %s could not be masked. '
             'Report version %s. '
             'Rerun the scan to generate a masked deployments report.'
             % (report.id,
                report.report_version)}
    return(Response(error,
                    status=status.HTTP_428_PRECONDITION_REQUIRED))


def build_cached_json_report(report, mask_report):
    """Create a count report based on the fingerprints and the group.

    :param report: the DeploymentsReport used to group count
    :param mask_report: <boolean> bool associated with whether
        or not we should mask the report.
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    if validate_query_param_bool(mask_report):
        if report.cached_masked_fingerprints:
            system_fingerprints = json.loads(
                report.cached_masked_fingerprints)
        else:
            return None
    else:
        system_fingerprints = json.loads(
            report.cached_fingerprints)
    return {
        'report_id': report.id,
        'status': report.status,
        'report_type': report.report_type,
        'report_version': report.report_version,
        'report_platform_id': str(report.report_platform_id),
        'system_fingerprints': system_fingerprints}
