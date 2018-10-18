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
from api.details_report.util import (create_details_report,
                                     validate_details_report_json)
from api.models import (DetailsReport,
                        ScanJob,
                        ScanTask)
from api.serializers import (DetailsReportSerializer,
                             ScanJobSerializer)
from api.signal.scanjob_signal import (start_scan)

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes)
from rest_framework.permissions import IsAuthenticated
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

    details_report_json = {'sources': sources}
    has_errors, validation_result = validate_details_report_json(
        details_report_json)
    if has_errors:
        message = _(messages.REPORT_MERGE_NO_RESULTS % validation_result)
        error.get('reports').append(message)
        raise ValidationError(error)

    # Create FC model and save data
    details_report = create_details_report(details_report_json)
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
    serializer = DetailsReportSerializer(details_report)
    result = serializer.data
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['get', 'put', 'post'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def async_merge_reports(request, pk=None):
    """Merge reports asynchronously."""
    # pylint: disable=invalid-name
    if request.method == 'GET':
        return _get_async_merge_report_status(pk)

    # is POST
    if pk is not None:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request.method == 'PUT':
        reports = validate_merge_report(request.data)
        sources = []
        for report in reports:
            sources = sources + report.get_sources()

        details_report_json = {'sources': sources}
        return _create_async_merge_report_job(details_report_json)

    # Post is last case
    return _create_async_merge_report_job(request.data)


def _get_async_merge_report_status(merge_job_id):
    """Retrieve merge report job status.

    :param merge_job_id: ScanJob id for this merge.
    :returns: Response for http request
    """
    merge_job = get_object_or_404(ScanJob.objects.all(), pk=merge_job_id)
    if merge_job.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
        return Response(status=status.HTTP_404_NOT_FOUND)
    job_serializer = ScanJobSerializer(merge_job)
    response_data = job_serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


def _create_async_merge_report_job(details_report_data):
    """Retrieve merge report job status.

    :param details_report_data: Details report data to fingerprint
    :returns: Response for http request
    """
    has_errors, validation_result = validate_details_report_json(
        details_report_data)
    if has_errors:
        return Response(validation_result,
                        status=status.HTTP_400_BAD_REQUEST)

    # Create FC model and save data
    details_report = create_details_report(details_report_data)

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
