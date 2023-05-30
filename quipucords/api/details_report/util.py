"""Util for validating and persisting source facts."""

import csv
import logging
from io import StringIO

from django.utils.translation import gettext as _

from api import messages
from api.common.common_report import CSVHelper, create_report_version, sanitize_row
from api.common.util import mask_data_general, validate_query_param_bool
from api.models import DetailsReport, ScanTask, ServerInformation
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
    """Validate details_report field.

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


def create_details_report(report_version, json_details_report):
    """Create details report.

    Fact collection consists of a DetailsReport record
    :param report_version: major.minor.patch version of report.
    :param json_details_report: dict representing a details report
    :returns: The newly created DetailsReport
    """
    # Create new details report
    serializer = DetailsReportSerializer(data=json_details_report)
    if serializer.is_valid():
        details_report = serializer.save()
        # removed by serializer since it is read-only.  Set again.
        details_report.report_version = report_version
        details_report.save()
        logger.debug("Fact collection created: %s", details_report)
        return details_report

    logger.error("Details report could not be persisted.")
    logger.error("Invalid json_details_report: %s", json_details_report)
    logger.error("DetailsReport errors: %s", serializer.errors)

    return None


def create_details_csv(details_report_dict, request):  # noqa: C901
    """Create details csv."""
    report_id = details_report_dict.get("report_id")
    if report_id is None:
        return None

    details_report = DetailsReport.objects.filter(report_id=report_id).first()
    if details_report is None:
        return None
    mask_report = request.query_params.get("mask", False)
    # Check for a cached copy of csv
    cached_csv = details_report.cached_csv
    if validate_query_param_bool(mask_report):
        cached_csv = details_report.cached_masked_csv
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
                details_report.report_type,
                details_report.report_version,
                details_report.report_platform_id,
                0,
            ]
        )
        return details_report_csv_buffer.getvalue()

    csv_writer.writerow(
        [
            report_id,
            details_report.report_type,
            details_report.report_version,
            details_report.report_platform_id,
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
    if validate_query_param_bool(mask_report):
        details_report.cached_masked_csv = cached_csv
    else:
        details_report.cached_csv = cached_csv
    details_report.save()

    return cached_csv


def mask_details_facts(report):
    """Mask sensitive facts from the details report.

    :param: report <dict> The details report to mask

    :returns: report <dict> The masked details report.
    """
    mac_and_ip_facts = [
        "ifconfig_ip_addresses",
        "ip_addresses",
        "vm.ip_addresses",
        "ifconfig_mac_addresses",
        "mac_addresses",
        "vm.mac_addresses",
    ]
    name_related_facts = [
        "vm.host_name",
        "vm.dns_name",
        "vm.cluster",
        "vm.name",
        "uname_hostname",
    ]
    sources = report.get("sources", [])
    for source in sources:
        facts = source.get("facts")
        source["facts"] = mask_data_general(facts, mac_and_ip_facts, name_related_facts)
    return report
