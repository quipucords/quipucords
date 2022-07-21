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
import logging
import os

from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from api.common.entities import ReportEntity
from api.exceptions import FailedDependencyError
from api.insights_report.insights_gzip_renderer import InsightsGzipRenderer
from api.insights_report.serializers import YupanaPayloadSerializer
from api.models import DeploymentsReport, SystemFingerprint
from api.user.authentication import QuipucordsExpiringTokenAuthentication

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
@renderer_classes((JSONRenderer, InsightsGzipRenderer, BrowsableAPIRenderer))
def insights(request, pk=None):
    """Lookup and return a insights system report."""
    deployment_report = get_object_or_404(
        DeploymentsReport.objects.only("id", "status"), pk=pk
    )
    _validate_deployment_report_status(deployment_report)
    report = _get_report(deployment_report)
    serializer = YupanaPayloadSerializer(report)
    return Response(serializer.data)


def _validate_deployment_report_status(deployment_report):
    if deployment_report.status != DeploymentsReport.STATUS_COMPLETE:
        raise FailedDependencyError(
            {
                "detail": f"Insights report {deployment_report.id} could not be "
                "created. See server logs."
            },
        )


def _get_report(deployment_report):
    try:
        report = ReportEntity.from_report_id(deployment_report.id)
    except SystemFingerprint.DoesNotExist as err:
        raise NotFound(
            f"Insights report {deployment_report.id} was not generated because "
            "there were 0 valid hosts. See server logs."
        ) from err

    return report
