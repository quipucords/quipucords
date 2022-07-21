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

"""View for system reports."""
import json
import logging
import os
import uuid

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.common_report import create_filename
from api.common.util import is_int
from api.insights_report.insights_gzip_renderer import InsightsGzipRenderer
from api.models import DeploymentsReport, ServerInformation
from api.user.authentication import QuipucordsExpiringTokenAuthentication
from quipucords import settings
from quipucords.environment import server_version

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


@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, InsightsGzipRenderer))
def insights(request, pk=None):
    """Lookup and return a insights system report."""
    if not is_int(pk):
        error = {
            'report_id': [_(messages.COMMON_ID_INV)]
        }
        raise ValidationError(error)

    report = get_object_or_404(DeploymentsReport.objects.all(), report_id=pk)
    if report.status != DeploymentsReport.STATUS_COMPLETE:
        return Response(
            {'detail': 'Insights report %s could not be created. '
                       'See server logs.' % report.details_report.id},
            status=status.HTTP_424_FAILED_DEPENDENCY)
    if report.cached_insights:
        return _create_report_slices(
            report, json.loads(report.cached_insights))

    error = {'detail':
             'Insights report %s was not generated. Report version %s.'
             'See server logs.' % (report.id,
                                   report.report_version)}
    return Response(error, status=404)


def _create_report_slices(report, insights_hosts):
    """Process facts and convert to fingerprints.

    :param report: DeploymentReport used to create slices
    :param insights_hosts: insights host JSON objects
    :returns: list containing report meta-data and report slices
    """
    # pylint: disable=too-many-locals
    slice_size_limit = settings.QPC_INSIGHTS_REPORT_SLICE_SIZE
    number_hosts = len(insights_hosts)

    if not number_hosts:
        error = {
            'detail':
            'Insights report %s was not generated because '
            'there were 0 valid hosts. '
            'Report version %s. See server logs.' % (report.id,
                                                     report.report_version)}
        return Response(error, status=404)

    if number_hosts % slice_size_limit:
        number_of_slices = number_hosts // slice_size_limit + 1
        hosts_per_slice = number_hosts // number_of_slices + 1
    else:
        number_of_slices = number_hosts // slice_size_limit
        hosts_per_slice = number_hosts // number_of_slices

    insights_report_pieces = {}
    metadata_report_slices = {}
    source_metadata = {
        'report_platform_id': str(report.report_platform_id),
        'report_type': 'insights',
        'report_version': report.report_version,
        'qpc_server_report_id': report.id,
        'qpc_server_version': server_version(),
        'qpc_server_id': ServerInformation.create_or_retreive_server_id()
    }
    metadata = {
        'report_id': str(report.report_platform_id),
        'host_inventory_api_version': '1.0',
        'source': 'qpc',
        'source_metadata': source_metadata,
        'report_slices': metadata_report_slices
    }
    insights_report_pieces[create_filename(
        'metadata', 'json', report.id)] = metadata
    list_slice_start = 0
    list_slice_end = hosts_per_slice
    for i in range(0, number_hosts, hosts_per_slice):
        hosts = []
        hosts = insights_hosts[list_slice_start:list_slice_end]

        report_slice_id = str(uuid.uuid4())
        report_slice_filename = create_filename(
            report_slice_id, 'json', report.id)
        metadata_report_slices[report_slice_id] = {
            'number_hosts': len(hosts)
        }
        report_slice = {
            'report_slice_id': report_slice_id,
            'hosts': hosts
        }
        insights_report_pieces[report_slice_filename] = report_slice
        list_slice_start = list_slice_end
        if list_slice_end + hosts_per_slice < number_hosts:
            list_slice_end = hosts_per_slice * (i + 2)
        else:
            list_slice_end = number_hosts
    return Response(insights_report_pieces)
