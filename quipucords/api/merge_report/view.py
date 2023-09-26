"""View for system reports."""
import logging

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.common_report import REPORT_TYPE_DETAILS
from api.common.util import is_int
from api.details_report.util import create_report, validate_details_report_json
from api.models import Report, ScanJob, ScanTask
from api.serializers import ScanJobSerializer
from api.signal.scanjob_signal import start_scan
from api.user.authentication import QuipucordsExpiringTokenAuthentication

logger = logging.getLogger(__name__)

auth_classes = (QuipucordsExpiringTokenAuthentication, SessionAuthentication)
perm_classes = (IsAuthenticated,)


@api_view(["get", "put", "post"])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def async_merge_reports(request, scan_job_id=None):
    """Merge reports asynchronously."""
    if request.method == "GET":
        return _get_async_merge_report_status(scan_job_id)

    # is POST
    if scan_job_id is not None:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request.method == "PUT":
        details_report_json = _convert_ids_to_json(request.data)
        return _create_async_merge_report_job(details_report_json)

    # Post is last case
    return _create_async_merge_report_job(request.data)


def _convert_ids_to_json(report_request_json):
    """Retrieve merge report job status.

    :param report_request_json: dict with report list of Report ids
    :returns: Report as dict
    """
    reports = _validate_merge_report(report_request_json)
    sources = []
    report_version = None
    report_type = None

    for report in reports:
        sources = sources + report.sources
        if not report_version and report.report_version:
            report_version = report.report_version
            report_type = REPORT_TYPE_DETAILS
    details_report_json = {"sources": sources}
    if report_version:
        details_report_json["report_version"] = report_version
        details_report_json["report_type"] = report_type
    return details_report_json


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
        details_report_data, True
    )
    if has_errors:
        return Response(validation_result, status=status.HTTP_400_BAD_REQUEST)

    details_report_data = _reconcile_source_versions(details_report_data)

    # Create FC model and save data
    report_version = details_report_data.get("report_version", None)
    details_report = create_report(report_version, details_report_data)

    # Create new job to run

    merge_job = ScanJob.objects.create(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, report=details_report
    )
    merge_job.log_current_status()
    job_serializer = ScanJobSerializer(merge_job)
    response_data = job_serializer.data

    # start fingerprint job
    start_scan.send(sender=__name__, instance=merge_job)

    return Response(response_data, status=status.HTTP_201_CREATED)


def _reconcile_source_versions(details_report_data):
    """Reconcile various source versions.

    Currently, we only have one version
        but this could change.  This function should handle it.
        This function assume validation was done previously.
    :param details_report_data: details report with versions
        in each source.  Required due to merging reports.
    :returns Transformed details report as dict.  Any transformation
        will be done.  All sources will be the same version.  Report
        also will have a version.
    """
    source_version = details_report_data["sources"][0]["report_version"]
    details_report_data["report_version"] = source_version
    return details_report_data


def _validate_merge_report(data):
    """Validate merge reports.

    :param data: dict with list of report ids
    :returns QuerySet Report
    """
    error = {"reports": []}
    if not isinstance(data, dict) or data.get("reports") is None:
        error.get("reports").append(_(messages.REPORT_MERGE_REQUIRED))
        raise ValidationError(error)
    report_ids = data.get("reports")
    if not isinstance(report_ids, list):
        error.get("reports").append(_(messages.REPORT_MERGE_NOT_LIST))
        raise ValidationError(error)

    report_id_count = len(report_ids)
    if report_id_count < 2:  # noqa: PLR2004
        error.get("reports").append(_(messages.REPORT_MERGE_TOO_SHORT))
        raise ValidationError(error)

    non_integer_values = [
        report_id for report_id in report_ids if not is_int(report_id)
    ]
    if bool(non_integer_values):
        error.get("reports").append(_(messages.REPORT_MERGE_NOT_INT))
        raise ValidationError(error)

    report_ids = [int(report_id) for report_id in report_ids]
    unique_id_count = len(set(report_ids))
    if unique_id_count != report_id_count:
        error.get("reports").append(_(messages.REPORT_MERGE_NOT_UNIQUE))
        raise ValidationError(error)

    reports = Report.objects.filter(pk__in=report_ids).order_by("-id")
    actual_report_ids = [report.id for report in reports]
    missing_reports = set(report_ids) - set(actual_report_ids)
    if bool(missing_reports):
        message = _(messages.REPORT_MERGE_NOT_FOUND) % (
            ", ".join([str(i) for i in missing_reports])
        )
        error.get("reports").append(message)
        raise ValidationError(error)

    return reports
