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

import api.messages as messages
from api.common.report_json_gzip_renderer import (ReportJsonGzipRenderer)
from api.common.util import CANONICAL_FACTS, INSIGHTS_FACTS, is_int
from api.models import (DeploymentsReport)

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import status
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

# pylint: disable=invalid-name
# Get an instance of a logger
logger = logging.getLogger(__name__)
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
                   ReportJsonGzipRenderer))
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
    report_dict = build_cached_insights_json_report(report)
    if report_dict.get('detail'):
        return Response(report_dict, status=404)
    return Response(report_dict)


def verify_report_hosts(hosts):
    """Verify that report hosts contain canonical facts.

    :param hosts: dictionary of hosts to verify
    returns: valid, invalid hosts
    """
    valid_hosts = []
    invalid_hosts = []
    missing_sys_platform_id = 0
    for host in hosts:
        found_facts = False
        if host.get('system_platform_id'):
            for fact in CANONICAL_FACTS:
                if host.get(fact):
                    found_facts = True
                    break
            if found_facts:
                valid_hosts.append(host)
            else:
                invalid_hosts.append(host.get('system_platform_id'))
        else:
            missing_sys_platform_id += 1
    message = '%d of %d hosts valid for Insights.' \
              % (len(valid_hosts),
                 len(valid_hosts) +
                 missing_sys_platform_id + len(invalid_hosts))
    logger.info(message)
    if invalid_hosts:
        logger.warning('The following hosts have no canonical '
                       'facts and will be excluded from the Insights '
                       'report: %s', str(invalid_hosts))
    if missing_sys_platform_id > 0:
        logger.error('%d hosts were missing the required '
                     '"system_platform_id" field.',
                     missing_sys_platform_id)
    return valid_hosts


def get_hosts_from_fp(report, host_dicts):
    """Generate insights report format from the hosts.

    :param report: the DeploymentsReport
    :param host_dicts: the hosts for the report
    :returns: json insights report format
    """
    valid_hosts = verify_report_hosts(host_dicts)
    insights_hosts = {}
    for host in valid_hosts:
        insights_host = {}
        for fact in INSIGHTS_FACTS:
            if host.get(fact):
                insights_host[fact] = host.get(fact)
        host_id = host.get('system_platform_id', None)
        if host_id:
            insights_hosts[host_id] = insights_host
    # save the insights format after generating
    report.cached_insights = json.dumps(insights_hosts)
    return insights_hosts


def build_cached_insights_json_report(report):
    """Create an insights report based on a deployments report.

    :param report: DeploymentsReport that is used to create insights report
    :returns: json report data
    :raises: Raises failed dependencies if no hosts have canonical facts
    """
    if report.cached_insights:
        insights_hosts = json.loads(report.cached_insights)
    else:
        insights_hosts = get_hosts_from_fp(
            report, json.loads(report.cached_fingerprints))
    if not insights_hosts:
        error_json = {
            'detail': 'Insights report could not be generated because '
                      'deployments report %s contained no hosts with '
                      'canonical facts' % str(report.id)
        }
        return error_json
    report_dict = {'report_id': report.id,
                   'status': report.status,
                   'report_type': 'insights',
                   'report_version': report.report_version,
                   'report_platform_id': str(report.report_platform_id),
                   'hosts': insights_hosts}

    return report_dict
