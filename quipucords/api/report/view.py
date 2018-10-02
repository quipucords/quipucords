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
import logging
import os

import api.messages as messages
from api.common.util import is_int
from api.fact.util import (create_fact_collection,
                           validate_fact_collection_json)
from api.models import (FactCollection,
                        ScanJob,
                        ScanTask,
                        SystemFingerprint)
from api.report.renderer import DeploymentCSVRenderer, DetailsCSVRenderer
from api.serializers import FactCollectionSerializer, FingerprintSerializer

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

from scanner.job import ScanJobRunner

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
                   DetailsCSVRenderer))
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
        json_details.pop('csv_content', None)
        json_details.pop('status', None)
    return Response(json_details)


@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   DeploymentCSVRenderer))
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

        report_fact_collection = get_object_or_404(
            FactCollection.objects.all(), pk=pk)
        return Response({'detail':
                         'Deployment report %s could not be created.'
                         '  See server logs.' % report_fact_collection.id},
                        status=status.HTTP_424_FAILED_DEPENDENCY)


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


@api_view(['PUT'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def merge(request):
    """Merge reports."""
    error = {
        'reports': []
    }
    reports = validate_merge_report(request.data)
    sources = []
    for report in reports:
        sources = sources + report.get_sources()

    fact_collection_json = {'sources': sources}
    has_errors, validation_result = validate_fact_collection_json(
        fact_collection_json)
    if has_errors:
        message = _(messages.REPORT_MERGE_NO_RESULTS % validation_result)
        error.get('reports').append(message)
        raise ValidationError(error)

    # Create FC model and save data
    fact_collection = create_fact_collection(fact_collection_json)
    scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                       fact_collection=fact_collection)
    scan_job.save()
    scan_job.queue()
    runner = ScanJobRunner(scan_job)
    runner.run()

    if scan_job.status != ScanTask.COMPLETED:
        raise Exception(scan_job.status_message)

    scan_job = ScanJob.objects.get(pk=scan_job.id)
    fact_collection = FactCollection.objects.get(pk=fact_collection.id)

    # Prepare REST response body
    serializer = FactCollectionSerializer(fact_collection)
    result = serializer.data
    return Response(result, status=status.HTTP_201_CREATED)


def validate_merge_report(data):
    """Validate merge reports."""
    # pylint: disable=no-self-use
    error = {
        'reports': []
    }
    if not isinstance(data, dict) or \
            data.get('reports') is None:
        error.get('reports').append(_(messages.REPORT_MERGE_REQUIRED))
        raise ValidationError(error)
    report_ids = data.get('reports')
    if not isinstance(report_ids, list):
        error.get('reports').append(_(messages.REPORT_MERGE_NOT_LIST))
        raise ValidationError(error)

    report_id_count = len(report_ids)
    if report_id_count < 2:
        error.get('reports').append(_(messages.REPORT_MERGE_TOO_SHORT))
        raise ValidationError(error)

    non_integer_values = [
        report_id for report_id in report_ids if not is_int(report_id)]
    if bool(non_integer_values):
        error.get('reports').append(_(messages.REPORT_MERGE_NOT_INT))
        raise ValidationError(error)

    report_ids = [int(report_id) for report_id in report_ids]
    unique_id_count = len(set(report_ids))
    if unique_id_count != report_id_count:
        error.get('reports').append(_(messages.REPORT_MERGE_NOT_UNIQUE))
        raise ValidationError(error)

    reports = FactCollection.objects.filter(pk__in=report_ids).order_by('-id')
    actual_report_ids = [report.id for report in reports]
    missing_reports = set(report_ids) - set(actual_report_ids)
    if bool(missing_reports):
        message = _(messages.REPORT_MERGE_NOT_FOUND) % (
            ', '.join([str(i) for i in missing_reports]))
        error.get('reports').append(message)
        raise ValidationError(error)

    return reports
