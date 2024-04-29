"""View for system reports."""

import logging
from itertools import chain

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api import messages
from api.common.util import is_int
from api.models import Report, ScanJob, ScanTask
from api.serializers import SimpleScanJobSerializer
from api.signal.scanjob_signal import start_scan

logger = logging.getLogger(__name__)


@api_view(["post"])
def async_merge_reports(request):
    """Merge reports asynchronously."""
    report_ids = _validate_report_ids(request.data)
    with transaction.atomic():
        merge_job = ScanJob.objects.create(
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            report=Report.objects.create(),
        )
        merge_job.copy_raw_facts_from_reports(report_ids)
    start_scan.send(sender=__name__, instance=merge_job)
    serializer = SimpleScanJobSerializer(merge_job)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def _validate_report_ids(data):
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

    actual_report_ids = set(
        chain.from_iterable(Report.objects.filter(pk__in=report_ids).values_list("id"))
    )
    missing_reports = set(report_ids) - set(actual_report_ids)
    if bool(missing_reports):
        message = _(messages.REPORT_MERGE_NOT_FOUND) % (
            ", ".join([str(i) for i in missing_reports])
        )
        error.get("reports").append(message)
        raise ValidationError(error)

    return report_ids
