"""Util for validating and persisting source facts."""

import csv
import logging
from io import StringIO

from django.utils.translation import gettext as _

from api import messages
from api.common.common_report import (
    REPORT_TYPE_DETAILS,
    CSVHelper,
    create_report_version,
    sanitize_row,
)
from api.models import (
    InspectGroup,
    InspectResult,
    RawFact,
    Report,
    ScanTask,
    ServerInformation,
)
from api.serializers import DetailsReportSerializer
from constants import DataSources

ERRORS_KEY = "errors"
INVALID_SOURCES_KEY = "invalid_sources"
VALID_SOURCES_KEY = "valid_sources"

# JSON attribute constants
REPORT_VERSION_KEY = "report_version"
REPORT_TYPE_KEY = "report_type"
SOURCES_KEY = "sources"
SOURCE_KEY = "source"
SERVER_ID_KEY = "server_id"
SOURCE_TYPE_KEY = "source_type"
SOURCE_NAME_KEY = "source_name"
FACTS_KEY = "facts"

logger = logging.getLogger(__name__)


def build_sources_from_tasks(tasks):
    """Build sources for a set of tasks.

    :param tasks: ScanTask objects used to build results
    :returns: dict containing sources structure for facts endpoint
    """
    server_id = ServerInformation.create_or_retrieve_server_id()
    sources = []
    for inspect_task in tasks:
        if inspect_task.scan_type != ScanTask.SCAN_TYPE_INSPECT:
            continue
        task_facts = inspect_task.get_facts()
        if task_facts:
            source = inspect_task.source
            if source is not None:
                source_dict = {
                    SERVER_ID_KEY: server_id,
                    REPORT_VERSION_KEY: create_report_version(),
                    SOURCE_NAME_KEY: source.name,
                    SOURCE_TYPE_KEY: source.source_type,
                    FACTS_KEY: task_facts,
                }
                sources.append(source_dict)
    return sources


def validate_details_report_json(details_report_json, external_json):
    """Validate details report.

    :param details_report_json: dict representing a details report
    :param external_json: bool True if json came in via REST
    :returns: bool indicating if there are errors and dict with result.
    """
    if not external_json and not details_report_json.get(REPORT_VERSION_KEY):
        # Internal JSON should always have this
        return True, {REPORT_VERSION_KEY: _(messages.FC_REQUIRED_ATTRIBUTE)}

    if not details_report_json.get(REPORT_TYPE_KEY):
        return True, {REPORT_TYPE_KEY: _(messages.FC_REQUIRED_ATTRIBUTE)}

    if not details_report_json.get(SOURCES_KEY):
        return True, {SOURCES_KEY: _(messages.FC_REQUIRED_ATTRIBUTE)}

    return _validate_sources_json(details_report_json.get(SOURCES_KEY))


def _validate_sources_json(sources_json):
    """Validate sources field.

    :param sources_json: list of sources.  Each source is a dict.
    :returns: bool indicating if there are errors and
    dict with 2 lists.  Valid and invalid sources.
    """
    valid_sources = []
    invalid_sources = []
    has_errors = False
    for source_json in sources_json:
        source_error, result = _validate_source_json(source_json)
        if source_error:
            has_errors = True
            invalid_sources.append(result)
        else:
            valid_sources.append(source_json)

    return has_errors, {
        VALID_SOURCES_KEY: valid_sources,
        INVALID_SOURCES_KEY: invalid_sources,
    }


def _validate_source_json(source_json):
    """Validate source fields.

    :param source_json: The dict representing facts for a source
    :returns: bool indicating if there are errors and
    dict with error result or None.
    """
    invalid_field_obj = {}
    has_error = False

    report_version = source_json.get(REPORT_VERSION_KEY)
    if not report_version:
        has_error = True
        invalid_field_obj[REPORT_VERSION_KEY] = _(messages.FC_REQUIRED_ATTRIBUTE)

    server_id = source_json.get(SERVER_ID_KEY)
    if not server_id:
        has_error = True
        invalid_field_obj[SERVER_ID_KEY] = _(messages.FC_REQUIRED_ATTRIBUTE)

    source_type = source_json.get(SOURCE_TYPE_KEY)
    source_name = source_json.get(SOURCE_NAME_KEY)

    if not source_name:
        has_error = True
        invalid_field_obj[SOURCE_NAME_KEY] = _(messages.FC_REQUIRED_ATTRIBUTE)

    if not source_type:
        has_error = True
        invalid_field_obj[SOURCE_TYPE_KEY] = _(messages.FC_REQUIRED_ATTRIBUTE)

    if not has_error and not isinstance(source_name, str):
        has_error = True
        invalid_field_obj[SOURCE_NAME_KEY] = _(messages.FC_SOURCE_NAME_NOT_STR)

    if not has_error and source_type not in DataSources:
        has_error = True
        valid_choices = ", ".join(DataSources.values)
        invalid_field_obj[SOURCE_TYPE_KEY] = _(
            messages.FC_MUST_BE_ONE_OF % valid_choices
        )

    facts = source_json.get(FACTS_KEY)
    if not facts:
        has_error = True
        invalid_field_obj[FACTS_KEY] = _(messages.FC_REQUIRED_ATTRIBUTE)

    if has_error:
        error_json = {}
        error_json[SOURCE_KEY] = source_json
        error_json[ERRORS_KEY] = invalid_field_obj
        return True, error_json
    return False, None


def create_report(
    *, report_version, json_details_report, scan_job, raise_exception=False
):
    """Create report.

    Fact collection consists of a Report record
    :param report_version: major.minor.patch version of report.
    :param json_details_report: dict representing a details report
    :param scan_job: ScanJob instance in which results will be attached
    :param raise_exception: raise exception on validation error
    :returns: The newly created Report
    """
    # Create new details report
    serializer = DetailsReportSerializer(data=json_details_report)
    if serializer.is_valid(raise_exception=raise_exception):
        sources = serializer.validated_data.pop("sources")
        report = serializer.save()
        # removed by serializer since it is read-only.  Set again.
        report.report_version = report_version
        report.save()
        scan_job.report = report
        scan_job.save()
        scan_task = ScanTask.objects.create(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            status=ScanTask.COMPLETED,
            status_message=_(messages.ST_STATUS_MSG_COMPLETED),
            sequence_number=1,
        )
        for source_dict in sources:
            inspect_group = InspectGroup.objects.create(
                source_type=source_dict["source_type"],
                source_name=source_dict["source_name"],
                server_id=source_dict["server_id"],
                server_version=source_dict["report_version"],
            )
            inspect_group.tasks.add(scan_task)
            for fact_dict in source_dict["facts"]:
                inspect_result = InspectResult.objects.create(
                    inspect_group=inspect_group
                )
                raw_facts = [
                    RawFact(name=k, value=v, inspect_result=inspect_result)
                    for k, v in fact_dict.items()
                ]
                RawFact.objects.bulk_create(raw_facts)
        logger.debug("Fact collection created: %s", report)
        return report

    logger.error("Report could not be persisted.")
    logger.error("Invalid json_details_report: %s", json_details_report)
    # seriously? this is used in a view and the best we can do is LOG serializer
    # errors instead of returning them in a error response?!
    logger.error("Report errors: %s", serializer.errors)

    return None


def create_details_csv(details_report_dict):  # noqa: C901
    """Create details csv."""
    report_id = details_report_dict.get("report_id")
    if report_id is None:
        return None
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return None
    # Check for a cached copy of csv
    cached_csv = report.cached_csv
    if cached_csv:
        logger.info("Using cached csv results for details report %d", report_id)
        return cached_csv
    logger.info("No cached csv results for details report %d", report_id)

    csv_helper = CSVHelper()
    details_report_csv_buffer = StringIO()
    csv_writer = csv.writer(details_report_csv_buffer, delimiter=",")

    sources = details_report_dict.get("sources")

    csv_writer.writerow(
        [
            "Report ID",
            "Report Type",
            "Report Version",
            "Report Platform ID",
            "Number Sources",
        ]
    )
    if sources is None:
        csv_writer.writerow(
            [
                report_id,
                REPORT_TYPE_DETAILS,
                report.report_version,
                report.report_platform_id,
                0,
            ]
        )
        return details_report_csv_buffer.getvalue()

    csv_writer.writerow(
        [
            report_id,
            REPORT_TYPE_DETAILS,
            report.report_version,
            report.report_platform_id,
            len(sources),
        ]
    )
    csv_writer.writerow([])
    csv_writer.writerow([])

    for source in sources:
        csv_writer.writerow(["Source"])
        csv_writer.writerow(["Server Identifier", "Source Name", "Source Type"])
        csv_writer.writerow(
            [
                source.get("server_id"),
                source.get("source_name"),
                source.get("source_type"),
            ]
        )
        csv_writer.writerow(["Facts"])
        fact_list = source.get("facts")
        if not fact_list:
            # write a space line and move to next
            csv_writer.writerow([])
            continue
        headers = csv_helper.generate_headers(fact_list)
        csv_writer.writerow(headers)

        for fact in fact_list:
            row = []
            for header in headers:
                fact_value = fact.get(header)
                row.append(csv_helper.serialize_value(header, fact_value))

            csv_writer.writerow(sanitize_row(row))

        csv_writer.writerow([])
        csv_writer.writerow([])

    logger.info("Caching csv results for details report %d", report_id)
    cached_csv = details_report_csv_buffer.getvalue()
    report.cached_csv = cached_csv
    report.save()

    return cached_csv
