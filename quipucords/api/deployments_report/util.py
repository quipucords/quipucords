"""Util for deployments report."""

import csv
import logging
from copy import deepcopy
from io import StringIO

from api.common.common_report import CSVHelper, sanitize_row
from api.models import DeploymentsReport, SystemFingerprint
from constants import DataSources

logger = logging.getLogger(__name__)

DETECTION_KEY_PREFIX = "detection"
SOURCES_KEY = "sources"


def _get_detection_keys():
    return (
        f"{DETECTION_KEY_PREFIX}-{data_source}" for data_source in DataSources.values
    )


def compute_source_info(sources):
    """Detect scan source types."""
    result = {
        SOURCES_KEY: [],
        **{
            source_detection_key: False
            for source_detection_key in _get_detection_keys()
        },
    }

    for source in sources:
        source_type = source.get("source_type")
        if source_type in DataSources:
            result[f"{DETECTION_KEY_PREFIX}-{source_type}"] = True
        result[SOURCES_KEY].append(source.get("source_name"))
    return result


def create_deployments_csv(deployments_report_dict):  # noqa: PLR0912, PLR0915, C901
    """Create deployments report csv."""
    deployments_report_dict = deepcopy(deployments_report_dict)
    source_headers = {SOURCES_KEY, *_get_detection_keys()}
    report_id = deployments_report_dict.get("report_id")
    if report_id is None:
        return None

    deployment_report = DeploymentsReport.objects.filter(report_id=report_id).first()
    if deployment_report is None:
        return None

    # Check for a cached copy of csv
    cached_csv = deployment_report.cached_csv
    if cached_csv:
        logger.info("Using cached csv results for deployment report %d", report_id)
        return cached_csv
    logger.info("No cached csv results for deployment report %d", report_id)

    csv_helper = CSVHelper()
    deployment_report_buffer = StringIO()
    csv_writer = csv.writer(deployment_report_buffer, delimiter=",")

    csv_writer.writerow(
        ["Report ID", "Report Type", "Report Version", "Report Platform ID"]
    )
    csv_writer.writerow(
        [
            report_id,
            deployment_report.report_type,
            deployment_report.report_version,
            deployment_report.report_platform_id,
        ]
    )
    csv_writer.writerow([])
    csv_writer.writerow([])

    systems_list = deployments_report_dict.get("system_fingerprints")
    if not systems_list:
        return None

    csv_writer.writerow(["System Fingerprints:"])

    valid_fact_attributes = {
        field.name for field in SystemFingerprint._meta.get_fields()
    }

    # Add fields to just one fingerprint
    system = systems_list[0]
    for attr in valid_fact_attributes:
        if not system.get(attr, None):
            system[attr] = None

    headers = csv_helper.generate_headers(
        systems_list,
        exclude={
            "id",
            "report_id",
            "metadata",
            "deployment_report",
            "cpu_core_per_socket",
            "system_purpose",
        },
    )
    if SOURCES_KEY in headers:
        headers += source_headers
        headers = sorted(list(set(headers)))

    # Add source headers
    csv_writer.writerow(headers)
    for system in systems_list:
        row = []
        system_sources = system.get(SOURCES_KEY)
        if system_sources is not None:
            sources_info = compute_source_info(system_sources)
        else:
            sources_info = None
        for header in headers:
            fact_value = None
            if header in source_headers:
                if sources_info is not None:
                    fact_value = sources_info.get(header)
            elif header == "entitlements":
                fact_value = system.get(header)
                if fact_value:
                    for entitlement in fact_value:
                        entitlement.pop("metadata")
            else:
                fact_value = system.get(header)
            row.append(csv_helper.serialize_value(header, fact_value))
        csv_writer.writerow(sanitize_row(row))

    csv_writer.writerow([])
    logger.info("Caching csv results for deployment report %d", report_id)
    cached_csv = deployment_report_buffer.getvalue()
    deployment_report.cached_csv = cached_csv
    deployment_report.save()
    return cached_csv
