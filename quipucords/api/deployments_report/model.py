"""Models system fingerprints."""

import json
import logging
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.db import models

from api.common.common_report import REPORT_TYPE_CHOICES, REPORT_TYPE_DEPLOYMENT
from api.common.models import BaseModel
from fingerprinter.constants import (
    ENTITLEMENTS_KEY,
    META_DATA_KEY,
    PRODUCTS_KEY,
    SOURCES_KEY,
)

logger = logging.getLogger(__name__)


def cached_files_path() -> Path:
    """Get the directory path for the cached report files."""
    return settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR


CACHED_FILE_NAME_FORMAT = "deployments-report-{id}-{unixtime}.{extension}"


class DeploymentsReport(BaseModel):
    """Represents deployment report."""

    report_type = models.CharField(
        max_length=11, choices=REPORT_TYPE_CHOICES, default=REPORT_TYPE_DEPLOYMENT
    )
    report_version = models.CharField(max_length=64, null=False)
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)

    STATUS_PENDING = "pending"
    STATUS_FAILED = "failed"
    STATUS_COMPLETE = "completed"
    STATUS_CHOICES = (
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_FAILED, STATUS_FAILED),
        (STATUS_COMPLETE, STATUS_COMPLETE),
    )

    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    cached_fingerprints_file_path = models.FilePathField(
        null=True, blank=True, path=cached_files_path, max_length=255
    )
    cached_csv_file_path = models.FilePathField(
        null=True, blank=True, path=cached_files_path, max_length=255
    )

    @property
    def cached_fingerprints(self) -> dict | None:
        """Return cached fingerprints data if it exists."""
        if not self.cached_fingerprints_file_path:
            return None
        file_path = Path(self.cached_fingerprints_file_path).absolute()
        if file_path.parent != cached_files_path():
            # Check to protect against potentially malicious filesystem access.
            message = (
                "Unsupported parent path for DeploymentsReport "
                f"{self.id} cached_fingerprints file: {file_path}"
            )
            logger.error(message)
            raise PermissionError(message)
        try:
            with file_path.open("r") as f:
                return json.load(f)
        except FileNotFoundError as e:
            logger.exception(e)
            logger.error(
                "Cached fingerprints file for DeploymentsReport %s not found at '%s'",
                self.id,
                file_path,
            )
            raise

    @cached_fingerprints.setter
    def cached_fingerprints(self, data):
        """Save cached fingerprints data."""
        file_path = cached_files_path() / CACHED_FILE_NAME_FORMAT.format(
            id=self.id, unixtime=time.time(), extension="json"
        )
        if file_path.exists():
            logger.warning("Overwriting existing file at %s", file_path)
        with file_path.open("w") as f:
            json.dump(data, f)
        self.cached_fingerprints_file_path = file_path

    @property
    def cached_csv(self):
        """Return cached csv data if it exists."""
        if not self.cached_csv_file_path:
            return None
        file_path = Path(self.cached_csv_file_path).absolute()
        if file_path.parent != cached_files_path():
            # Check to protect against potentially malicious filesystem access.
            message = (
                "Unsupported parent path for DeploymentsReport "
                f"{self.id} cached_csv file: {file_path}"
            )
            logger.error(message)
            raise PermissionError(message)
        try:
            with file_path.open("r", newline="") as f:
                # I hate `newline=''` but we need this for compatibility
                # because we write \r\n into the CSV file, but by default,
                # python wants to strip the extra `\r` from `\r\n`.
                # See also: https://docs.python.org/3.12/library/functions.html#open
                return f.read()
        except FileNotFoundError as e:
            logger.exception(e)
            logger.error(
                "Cached CSV file for DeploymentsReport %s not found at '%s'",
                self.id,
                self.cached_csv_file_path,
            )
            raise

    @cached_csv.setter
    def cached_csv(self, data):
        """Save cached csv data."""
        file_path = cached_files_path() / CACHED_FILE_NAME_FORMAT.format(
            id=self.id, unixtime=time.time(), extension="csv"
        )
        if file_path.exists():
            logger.warning("Overwriting existing file at %s", file_path)
        with file_path.open("w") as f:
            f.write(data)
        self.cached_csv_file_path = file_path


class SystemFingerprint(BaseModel):
    """Represents system fingerprint."""

    # Important: If you add a DATE field, add it to list
    DATE_FIELDS = ["system_last_checkin_date", "system_creation_date"]

    BARE_METAL = "bare_metal"
    UNKNOWN = "unknown"
    VIRTUALIZED = "virtualized"
    HYPERVISOR = "hypervisor"

    INFRASTRUCTURE_TYPE = (
        (BARE_METAL, "Bare Metal"),
        (VIRTUALIZED, "Virtualized"),
        (HYPERVISOR, "Hypervisor"),
        (UNKNOWN, "Unknown"),
    )

    # Scan information
    deployment_report = models.ForeignKey(
        DeploymentsReport, models.CASCADE, related_name="system_fingerprints"
    )

    # Common facts
    name = models.CharField(max_length=256, unique=False, blank=True, null=True)
    os_name = models.CharField(max_length=64, unique=False, blank=True, null=True)
    os_release = models.CharField(max_length=128, unique=False, blank=True, null=True)
    os_version = models.CharField(max_length=64, unique=False, blank=True, null=True)

    infrastructure_type = models.CharField(max_length=12, choices=INFRASTRUCTURE_TYPE)

    cloud_provider = models.CharField(
        max_length=16, unique=False, blank=True, null=True
    )

    mac_addresses = models.JSONField(unique=False, blank=True, null=True)
    ip_addresses = models.JSONField(unique=False, blank=True, null=True)

    cpu_count = models.PositiveIntegerField(unique=False, blank=True, null=True)

    architecture = models.CharField(max_length=64, unique=False, blank=True, null=True)
    system_memory_bytes = models.PositiveBigIntegerField(
        unique=False, blank=True, null=True
    )

    # Network scan facts
    bios_uuid = models.CharField(max_length=36, unique=False, blank=True, null=True)
    subscription_manager_id = models.CharField(
        max_length=36, unique=False, blank=True, null=True
    )

    cpu_socket_count = models.PositiveIntegerField(unique=False, blank=True, null=True)
    cpu_core_count = models.FloatField(unique=False, blank=True, null=True)
    cpu_core_per_socket = models.PositiveIntegerField(
        unique=False, blank=True, null=True
    )
    cpu_hyperthreading = models.BooleanField(null=True)

    installed_products = models.JSONField(unique=False, blank=True, null=True)

    system_creation_date = models.DateField(blank=True, null=True)
    system_last_checkin_date = models.DateField(blank=True, null=True)

    system_purpose = models.TextField(unique=False, blank=True, null=True)
    system_role = models.CharField(max_length=128, unique=False, blank=True, null=True)
    system_addons = models.TextField(unique=False, blank=True, null=True)
    system_service_level_agreement = models.CharField(
        max_length=128, unique=False, blank=True, null=True
    )
    system_usage_type = models.CharField(
        max_length=128, unique=False, blank=True, null=True
    )
    insights_client_id = models.CharField(
        max_length=128, unique=False, blank=True, null=True
    )

    virtualized_type = models.CharField(
        max_length=64, unique=False, blank=True, null=True
    )
    virtual_host_name = models.CharField(
        max_length=128, unique=False, blank=True, null=True
    )
    virtual_host_uuid = models.CharField(
        max_length=36, unique=False, blank=True, null=True
    )

    system_user_count = models.PositiveIntegerField(unique=False, blank=True, null=True)
    user_login_history = models.JSONField(unique=False, blank=True, null=True)

    # VCenter scan facts
    vm_state = models.CharField(max_length=24, unique=False, blank=True, null=True)
    vm_uuid = models.CharField(max_length=36, unique=False, blank=True, null=True)
    vm_dns_name = models.CharField(max_length=256, unique=False, blank=True, null=True)
    vm_host_socket_count = models.PositiveIntegerField(
        unique=False, blank=True, null=True
    )
    vm_host_core_count = models.PositiveIntegerField(
        unique=False, blank=True, null=True
    )
    vm_cluster = models.CharField(max_length=128, unique=False, blank=True, null=True)
    vm_datacenter = models.CharField(
        max_length=128, unique=False, blank=True, null=True
    )

    # Red Hat facts
    is_redhat = models.BooleanField(null=True)
    redhat_certs = models.TextField(unique=False, blank=True, null=True)
    redhat_package_count = models.PositiveIntegerField(
        unique=False, blank=True, null=True
    )

    metadata = models.JSONField(unique=False, null=False, default=dict)
    sources = models.JSONField(unique=False, null=False, default=list)
    etc_machine_id = models.CharField(
        max_length=48, unique=False, blank=True, null=True
    )

    @classmethod
    def get_valid_fact_names(cls):
        """All expected fact names."""
        non_fact_fields = {
            "id",
            "deployment_report",
            "created_at",
            "updated_at",
            META_DATA_KEY,
            SOURCES_KEY,
            ENTITLEMENTS_KEY,
            PRODUCTS_KEY,
        }
        return {field.name for field in cls._meta.get_fields()} - non_fact_fields


class Product(BaseModel):
    """Represents a product."""

    PRESENT = "present"
    ABSENT = "absent"
    POTENTIAL = "potential"
    UNKNOWN = "unknown"
    PRESENCE_TYPE = (
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (POTENTIAL, "Potential"),
        (UNKNOWN, "Unknown"),
    )

    fingerprint = models.ForeignKey(
        SystemFingerprint, models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=256, unique=False, null=False)
    version = models.JSONField(unique=False, null=True)
    presence = models.CharField(max_length=10, choices=PRESENCE_TYPE)

    metadata = models.JSONField(unique=False, null=False, default=dict)


class Entitlement(BaseModel):
    """Represents a Entitlement."""

    fingerprint = models.ForeignKey(
        SystemFingerprint, models.CASCADE, related_name="entitlements"
    )
    name = models.CharField(max_length=256, unique=False, null=True)
    entitlement_id = models.CharField(max_length=256, unique=False, null=True)

    metadata = models.JSONField(unique=False, null=False, default=dict)
