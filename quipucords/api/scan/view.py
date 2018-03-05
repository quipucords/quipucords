#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Describes the views associated with the API models."""

import os
import logging
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes)
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import ValidationError
from rest_framework_expiring_authtoken.authentication import \
    ExpiringTokenAuthentication
from django.db.models import Q
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet)
import api.messages as messages
from api.common.util import is_int
from api.common.pagination import StandardResultsSetPagination
from api.models import (Scan, ScanTask, ScanJob, Source)
from api.serializers import (ScanSerializer, ScanJobSerializer)
from api.scanjob.serializer import expand_scanjob
from api.signals.scanjob_signal import (start_scan, cancel_scan)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-many-branches,invalid-name

SOURCES_KEY = 'sources'
MOST_RECENT = 'most_recent'
JOBS_KEY = 'jobs'

##################################################
# Independent jobs route
##################################################
JOB_ORDER_FIELDS = ['id',
                    '-id',
                    'scan_type',
                    '-scan_type',
                    'status',
                    '-status',
                    'start_time',
                    '-start_time',
                    'end_time',
                    '-end_time']
JOB_VALID_STATUS = [ScanTask.CREATED,
                    ScanTask.PENDING,
                    ScanTask.RUNNING,
                    ScanTask.PAUSED,
                    ScanTask.CANCELED,
                    ScanTask.COMPLETED,
                    ScanTask.FAILED]

authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'

if authentication_enabled:
    auth_classes = (ExpiringTokenAuthentication,
                    SessionAuthentication)
    perm_classes = (IsAuthenticated,)
else:
    auth_classes = ()
    perm_classes = ()


@api_view(['get', 'post'])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def jobs(request, pk=None):
    """Get the jobs of a scan."""
    # pylint: disable=invalid-name
    if pk is not None:
        if not is_int(pk):
            return Response(status=status.HTTP_404_NOT_FOUND)
    result = []
    scan = get_object_or_404(Scan.objects.all(), pk=pk)
    if request.method == 'GET':
        job_queryset = get_job_queryset_query_set(scan,
                                                  request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(job_queryset, request)

        if page is not None:
            serializer = ScanJobSerializer(page, many=True)
            for scan in serializer.data:
                json_scan = expand_scanjob(scan)
                result.append(json_scan)
            return paginator.get_paginated_response(serializer.data)

        for job in job_queryset:
            job_serializer = ScanJobSerializer(job)
            job_json = job_serializer.data
            job_json = expand_scanjob(job_serializer.data)
            result.append(job_json)
        return Response(result)
    else:
        job_data = {}
        job_data['scan'] = pk
        job_serializer = ScanJobSerializer(data=job_data)
        job_serializer.is_valid(raise_exception=True)
        job_serializer.save()
        scanjob_obj = ScanJob.objects.get(pk=job_serializer.data['id'])
        scanjob_obj.log_current_status()
        start_scan.send(sender=ScanViewSet.__class__, instance=scanjob_obj)

        return Response(job_serializer.data,
                        status=status.HTTP_201_CREATED)


def get_job_queryset_query_set(scan, query_params):
    """Build job queryset."""
    job_queryset = ScanJob.objects.filter(scan=scan)

    status_filter = query_params.get('status')
    if status_filter is not None and \
            status_filter.lower() in JOB_VALID_STATUS:
        job_queryset = job_queryset.filter(status=status_filter)

    ordering = query_params.get('ordering')
    if ordering is not None and ordering in JOB_ORDER_FIELDS:
        job_queryset = job_queryset.order_by(ordering)
    else:
        job_queryset = job_queryset.order_by('id')
    return job_queryset


def expand_scan(json_scan):
    """Expand the scan object's sources."""
    # pylint: disable=too-many-locals
    source_ids = json_scan.get(SOURCES_KEY, [])
    slim_sources = Source.objects.filter(
        pk__in=source_ids).values('id', 'name', 'source_type')
    if slim_sources:
        json_scan[SOURCES_KEY] = slim_sources

    scan_jobs = json_scan.get(JOBS_KEY)
    latest_job = None
    if bool(scan_jobs):
        latest_job = scan_jobs[0]
        latest_job = ScanJob.objects.filter(id=latest_job['id']).first()

    if latest_job is not None:
        systems_count, \
            systems_scanned, \
            systems_failed = latest_job.calculate_counts()
        report_id = latest_job.report_id
        start_time = latest_job.start_time
        end_time = latest_job.end_time
        systems_count = systems_count
        systems_scanned = systems_scanned
        systems_failed = systems_failed
        job_status = latest_job.status
        job_status_message = latest_job.status_message

        most_recent = {
            'id': latest_job.id,
        }

        if report_id is not None:
            most_recent['report_id'] = report_id
        if start_time is not None:
            most_recent['start_time'] = start_time
        if end_time is not None:
            most_recent['end_time'] = end_time
        if systems_count is not None:
            most_recent['systems_count'] = systems_count
        if systems_scanned is not None:
            most_recent['systems_scanned'] = systems_scanned
        if systems_failed is not None:
            most_recent['systems_failed'] = systems_failed
        if job_status_message is not None:
            most_recent['status_details'] = {
                'job_status_message': job_status_message}
        if job_status is not None:
            most_recent['status'] = job_status
            if job_status == ScanTask.FAILED:
                failed_tasks = latest_job.tasks.all().order_by(
                    'sequence_number')
                status_details = most_recent['status_details']
                for task in failed_tasks:
                    task_key = 'task_%s_status_message' % task.id
                    status_details[task_key] = task.status_message

        json_scan[MOST_RECENT] = most_recent

    return json_scan


class ScanFilter(FilterSet):
    """Filter for sources by name."""

    class Meta:
        """Metadata for filterset."""

        model = Scan
        fields = ['scan_type']


# pylint: disable=too-many-ancestors
class ScanViewSet(ModelViewSet):
    """A view set for Scan."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (ExpiringTokenAuthentication,
                                  SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = ScanFilter
    ordering_fields = ('id', 'name', 'scan_type')
    ordering = ('name',)

    # pylint: disable=unused-argument
    def create(self, request, *args, **kwargs):
        """Create a scan."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        json_scan = serializer.data
        json_scan = expand_scan(json_scan)
        return Response(json_scan, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request):  # pylint: disable=unused-argument
        """List the collection of scan."""
        result = []
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for scan in serializer.data:
                expand_scan(scan)
                result.append(scan)
            return self.get_paginated_response(serializer.data)

        for scan in queryset:
            serializer = ScanSerializer(scan)
            json_scan = serializer.data
            json_scan = expand_scan(json_scan)
            result.append(json_scan)
        return Response(result)

    # pylint: disable=unused-argument, arguments-differ
    def retrieve(self, request, pk=None):
        """Get a scan."""
        if not pk or (pk and not is_int(pk)):
            error = {
                'id': [_(messages.COMMON_ID_INV)]
            }
            raise ValidationError(error)

        scan = get_object_or_404(self.queryset, pk=pk)
        serializer = ScanSerializer(scan)
        json_scan = serializer.data
        expand_scan(json_scan)
        return Response(json_scan)

    @transaction.atomic
    def destroy(self, request, pk):
        """Delete a scan, its jobs, and the results."""
        # pylint: disable=too-many-nested-blocks
        try:
            scan = Scan.objects.get(pk=pk)
            logger.info('Deleting scan jobs associated with scan %s', pk)
            if scan.jobs is not None:
                jobs_to_cancel = scan.jobs.exclude(
                    Q(status=ScanTask.FAILED) |
                    Q(status=ScanTask.CANCELED) |
                    Q(status=ScanTask.COMPLETED))
                if jobs_to_cancel:
                    for job in jobs_to_cancel:
                        job.cancel()
                        cancel_scan.send(sender=self.__class__, instance=job)

                for job in scan.jobs.all():
                    logger.info('Deleting job %s and its results', job.id)
                    if job.connection_results is not None:
                        logger.info(
                            'Deleting connection results associated '
                            'with job %s', job.id)
                        for task_connection_result in \
                                job.connection_results.task_results.all():
                            task_connection_result.systems.all().delete()
                            task_connection_result.delete()

                    if job.inspection_results is not None:
                        logger.info(
                            'Deleting inspection results associated '
                            'with job %s', job.id)
                        for task_inspection_result in \
                                job.inspection_results.task_results.all():
                            logger.info(
                                'Deleting inspection results associated '
                                'with job %s', job.id)
                            for system in task_inspection_result.systems.all():
                                system.facts.all().delete()
                                system.delete()
                            task_inspection_result.delete()

                    if job.tasks is not None:
                        logger.info(
                            'Deleting scan tasks associated '
                            'with job %s', job.id)
                        job.tasks.all().delete()
                        job.delete()

            logger.info('Deleting scan %s', pk)
            scan.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Scan.DoesNotExist:
            raise Http404
