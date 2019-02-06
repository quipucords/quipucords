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
from api.common.util import is_int
from api.deployments_report.csv_renderer import (DeploymentCSVRenderer)
from api.models import (DeploymentsReport)

from django.core.exceptions import FieldError
from django.db.models import Count
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

    validate_filters(request.query_params)
    filters = filter_keys(request.query_params)
    report = get_object_or_404(DeploymentsReport.objects.all(), report_id=pk)
    if report.status != DeploymentsReport.STATUS_COMPLETE:
        return Response({'detail':
                         'Deployment report %s could not be created.'
                         '  See server logs.' % report.details_report.id},
                        status=status.HTTP_424_FAILED_DEPENDENCY)

    if request.query_params.get('group_count', None):
        report_dict = build_grouped_report(
            report, request.query_params.get('group_count'))
    elif filters:
        report_dict = build_filtered_report(report, filters)
    else:
        report_dict = build_cached_json_report(report)

    return Response(report_dict)


def validate_filters(filters):
    """Check the combination of filters are allowed.

    :param filters: report filters to checks
    :raises: Raises validation error if the combination of
    filters is not allowed.
    """
    filter_count = len(filters.keys())
    group_count_found = filters.get('group_count', None)
    if group_count_found is not None and filter_count > 1:
        error = {
            'query_params': [_(messages.REPORT_GROUP_COUNT_FILTER)]
        }
        raise ValidationError(error)


def filter_keys(filters):
    """Get the values to supply based on the filters.

    :param fiters: filters for the report
    :returns: list of keys to display in report
    """
    filter_list = []
    filters_clone = filters.copy()
    filters_clone.pop('group_count', None)
    for filter_key, filter_value in filters_clone.items():
        if (isinstance(filter_value, str) and
                filter_value.lower() == 'true'):
            filter_list.append(filter_key)
    return set(filter_list)


def build_report(report, fingerprint_dicts):
    """Create starter object for report json.

    :param report: the DeploymentsReport
    :param fingerprint_dicts: the fingerprints for the report
    :returns: json report start object
    """
    report_dict = {'report_id': report.id,
                   'status': report.status,
                   'report_type': report.report_type,
                   'report_version': report.report_version,
                   'report_platform_id': str(report.report_platform_id),
                   'system_fingerprints': fingerprint_dicts}
    return report_dict


def build_cached_json_report(report):
    """Create a count report based on the fingerprints and the group.

    :param report: the DeploymentsReport used to group count
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    return build_report(report, json.loads(report.cached_fingerprints))


def build_grouped_report(report, group):
    """Create a count report based on the fingerprints and the group.

    :param report: the DeploymentsReport used to group count
    :param group: the field to group and count on
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    try:

        # Group by field and count
        counts_by_group = report.system_fingerprints.all().values(
            group).annotate(total=Count(group))
    except FieldError:
        msg = _(messages.REPORT_GROUP_COUNT_FIELD % (group))
        error = {
            'query_params': [msg]
        }
        raise ValidationError(error)

    if not counts_by_group:
        return None

    # Build response dictionary
    fingerprints = []
    for group_count in counts_by_group:
        fingerprints.append(
            {
                group: group_count[group],
                'count': group_count['total']
            }
        )
    return build_report(report, fingerprints)


def build_filtered_report(report, filters):
    """Create a count report based on the fingerprints and the group.

    :param report: The DeploymentsReport used for filtered report
    :param filters: The values to display in report
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    try:
        # Group by field and count
        fingerprints = report.system_fingerprints.all().values(*filters)
    except FieldError:
        filter_string = '[%s]' % (', '.join(filters))
        msg = _(messages.REPORT_INVALID_FILTER_QUERY_PARAM % (filter_string))
        error = {
            'query_params': [msg]
        }
        raise ValidationError(error)

    # Build response dictionary
    return build_report(report, fingerprints)
