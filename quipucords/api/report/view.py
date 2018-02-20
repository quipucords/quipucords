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

"""View for system reports."""
import os
import logging
from django.utils.translation import ugettext as _
from django.db.models import Count
from django.core.exceptions import FieldError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import (api_view,
                                       renderer_classes,
                                       authentication_classes,
                                       permission_classes)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import (BrowsableAPIRenderer,
                                      JSONRenderer)
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from api.report.renderer import ReportCSVRenderer, FactCollectionCSVRenderer
from api.models import SystemFingerprint, FactCollection
from api.serializers import FingerprintSerializer, FactCollectionSerializer
import api.messages as messages
from api.common.util import is_int


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


# pylint: disable=C0103, W0613, R0201
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   FactCollectionCSVRenderer))
def details(request, pk=None):
    """Lookup and return a details system report."""
    if pk is not None:
        if not is_int(pk):
            error = {
                'report_id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)
    detail_data = get_object_or_404(FactCollection.objects.all(), pk=pk)
    serializer = FactCollectionSerializer(detail_data)
    json_details = serializer.data
    http_accept = request.META.get('HTTP_ACCEPT')
    if http_accept and 'text/csv' not in http_accept:
        json_details.pop('csv_content')
        json_details.pop('status')
    return Response(json_details)


@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   ReportCSVRenderer))
def deployments(request, pk=None):
    """Lookup and return a deployment system report."""
    validate_filters(request.query_params)

    if pk is not None:
        if not is_int(pk):
            error = {
                'report_id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        report = build_report(pk, request.query_params)
        if report is not None:
            return Response(report)
        return Response(status=status.HTTP_404_NOT_FOUND)


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


def build_grouped_report(report_id, fingerprints, group):
    """Create a count report based on the fingerprints and the group.

    :param report_id: the identifer for the report
    :param fingerprints: The system fingerprints used in the group count
    :param group: the field to group and count on
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    try:
        # Group by field and count
        counts_by_group = fingerprints.values(
            group).annotate(total=Count(group))
    except FieldError:
        msg = _(messages.REPORT_GROUP_COUNT_FIELD % (group))
        error = {
            'query_params': [msg]
        }
        raise ValidationError(error)

    if len(counts_by_group) is 0:
        return None

    # Build response dictionary
    report = {'report_id': report_id,
              'report': []}
    for group_count in counts_by_group:
        report['report'].append(
            {
                group: group_count[group],
                'count': group_count['total']
            }
        )
    return report


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


def build_report(report_id, filters):
    """Lookup system report by report_id.

    :param report_id: the identifer for the report
    :param fiters: filters for the report
    :returns: json report data
    """
    # We want aggregate counts on the fingerprints
    # Find all fingerprints with this report_id
    fingerprints = SystemFingerprint.objects.filter(
        report_id__id=report_id)

    if len(fingerprints) is 0:
        return None

    group = filters.get('group_count', None)
    if group is not None:
        return build_grouped_report(report_id,
                                    fingerprints,
                                    group)
    # Build response dictionary
    report = {'report_id': report_id,
              'report': []}
    filterkeys = filter_keys(filters)
    for fingerprint in fingerprints:
        serializer = FingerprintSerializer(fingerprint)
        if filterkeys == set():
            report['report'].append(serializer.data)
        else:
            filtered_data = {}
            for key in filterkeys:
                visible_data = serializer.data.get(key, None)
                filtered_data[key] = visible_data
            report['report'].append(filtered_data)
    return report
