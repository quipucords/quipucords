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
import json
import logging
import os

import api.messages as messages
from api.common.util import is_int
from api.fact.util import (create_fact_collection,
                           validate_fact_collection_json)
from api.models import (DeploymentsReport,
                        DetailsReport,
                        ScanJob,
                        ScanTask)
from api.report.cvs_renderer import DeploymentCSVRenderer, DetailsCSVRenderer
from api.serializers import (FactCollectionSerializer,
                             ScanJobSerializer)
from api.signal.scanjob_signal import (start_scan)

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
    detail_data = get_object_or_404(DetailsReport.objects.all(), report_id=pk)
    serializer = FactCollectionSerializer(detail_data)
    json_details = serializer.data
    http_accept = request.META.get('HTTP_ACCEPT')
    if http_accept and 'text/csv' not in http_accept:
        json_details.pop('cached_csv', None)
    return Response(json_details)


# pylint: disable=inconsistent-return-statements
@api_view(['GET'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
@renderer_classes((JSONRenderer, BrowsableAPIRenderer,
                   DeploymentCSVRenderer))
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

    # pylint: disable=no-else-return
    if request.query_params.get('group_count', None):
        report_dict = build_grouped_report(
            report, request.query_params.get('group_count'))
        return Response(report_dict)
    elif filters:
        report_dict = build_filtered_report(report, filters)
        return Response(report_dict)
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
                   'system_fingerprints': fingerprint_dicts}
    return report_dict


def build_cached_json_report(report):
    """Create a count report based on the fingerprints and the group.

    :param report: the DeploymentsReport used to group count
    :returns: json report data
    :raises: Raises validation error group_count on non-existent field.
    """
    return build_report(report, json.loads(report.cached_json))


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

    if len(counts_by_group) is 0:
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


@api_view(['PUT'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def sync_merge_reports(request):
    """Merge reports synchronously."""
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
    details_report = create_fact_collection(fact_collection_json)
    scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                       details_report=details_report)
    scan_job.save()
    scan_job.queue()
    runner = ScanJobRunner(scan_job)
    runner.run()

    if scan_job.status != ScanTask.COMPLETED:
        raise Exception(scan_job.status_message)

    scan_job = ScanJob.objects.get(pk=scan_job.id)
    details_report = DetailsReport.objects.get(pk=details_report.id)

    # Prepare REST response body
    serializer = FactCollectionSerializer(details_report)
    result = serializer.data
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['get', 'post'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def async_merge_reports(request, pk=None):
    """Merge reports asynchronously."""
    # pylint: disable=invalid-name
    if request.method == 'GET':
        merge_job = get_object_or_404(ScanJob.objects.all(), pk=pk)
        if merge_job.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
            return Response(status=status.HTTP_404_NOT_FOUND)
        job_serializer = ScanJobSerializer(merge_job)
        response_data = job_serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    # is POST
    if pk is not None:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    # Else post
    has_errors, validation_result = validate_fact_collection_json(
        request.data)
    if has_errors:
        return Response(validation_result,
                        status=status.HTTP_400_BAD_REQUEST)

    # Create FC model and save data
    details_report = create_fact_collection(request.data)

    # Create new job to run

    merge_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
                        details_report=details_report)
    merge_job.save()
    merge_job.log_current_status()
    job_serializer = ScanJobSerializer(merge_job)
    response_data = job_serializer.data

    # start fingerprint job
    start_scan.send(sender=__name__, instance=merge_job)

    return Response(response_data, status=status.HTTP_201_CREATED)


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

    reports = DetailsReport.objects.filter(pk__in=report_ids).order_by('-id')
    actual_report_ids = [report.id for report in reports]
    missing_reports = set(report_ids) - set(actual_report_ids)
    if bool(missing_reports):
        message = _(messages.REPORT_MERGE_NOT_FOUND) % (
            ', '.join([str(i) for i in missing_reports]))
        error.get('reports').append(message)
        raise ValidationError(error)

    return reports
