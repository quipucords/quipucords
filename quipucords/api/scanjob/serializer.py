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
"""Module for serializing all model object for database storage."""

from django.utils.translation import gettext as _
from rest_framework.serializers import (
    CharField,
    DateTimeField,
    IntegerField,
    PrimaryKeyRelatedField,
    ValidationError,
)

from api import messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.common.util import convert_to_int, is_int
from api.models import Scan, ScanJob, ScanTask, Source
from api.scan.serializer import ScanOptionsSerializer
from api.scantask.serializer import ScanTaskSerializer, SourceField

SCAN_KEY = "scan"
SOURCES_KEY = "sources"
TASKS_KEY = "tasks"
SYSTEMS_COUNT_KEY = "systems_count"
SYSTEMS_SCANNED_KEY = "systems_scanned"
SYSTEMS_FAILED_KEY = "systems_failed"
SYSTEMS_UNREACHABLE_KEY = "systems_unreachable"
SYSTEM_FINGERPRINTS_KEY = "system_fingerprint_count"


def expand_scanjob(json_scan):
    """Expand the source and calculate values.

    Take scan object with source ids and pull objects from db.
    create slim dictionary version of sources with name an value
    to return to user. Calculate systems_count, systems_scanned,
    systems_failed values from tasks.
    """
    source_ids = json_scan.get(SOURCES_KEY, [])
    slim_sources = Source.objects.filter(pk__in=source_ids).values(
        "id", "name", "source_type"
    )
    if slim_sources:
        json_scan[SOURCES_KEY] = slim_sources

    scan_id = json_scan.get(SCAN_KEY)
    slim_scan = Scan.objects.filter(pk=scan_id).values("id", "name").first()
    json_scan[SCAN_KEY] = slim_scan

    if json_scan.get(TASKS_KEY):
        scan_job = ScanJob.objects.get(pk=json_scan.get("id"))
        (
            systems_count,
            systems_scanned,
            systems_failed,
            systems_unreachable,
            system_fingerprint_count,
        ) = scan_job.calculate_counts()

        json_scan[SYSTEMS_COUNT_KEY] = systems_count
        json_scan[SYSTEMS_SCANNED_KEY] = systems_scanned
        json_scan[SYSTEMS_FAILED_KEY] = systems_failed
        json_scan[SYSTEMS_UNREACHABLE_KEY] = systems_unreachable

        json_scan[SYSTEM_FINGERPRINTS_KEY] = system_fingerprint_count
        for task_json in json_scan[TASKS_KEY]:
            if task_json["scan_type"] == ScanTask.SCAN_TYPE_FINGERPRINT:
                task_json[SYSTEM_FINGERPRINTS_KEY] = system_fingerprint_count
    return json_scan


class ScanField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_internal_value(self, data):
        """Create internal value."""
        if not is_int(data):
            raise ValidationError(_(messages.SJ_SCAN_IDS_INV))
        int_data = convert_to_int(data)
        actual_scan = Scan.objects.filter(id=int_data).first()
        if actual_scan is None:
            raise ValidationError(_(messages.SJ_SCAN_DO_NOT_EXIST % int_data))
        return actual_scan

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Scan):
            display = f"Scan: {instance.name}"
        return display


class TaskField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_representation(self, value):
        """Create output representation."""
        serializer = ScanTaskSerializer(value)
        return serializer.data


class ScanJobSerializer(NotEmptySerializer):
    """Serializer for the ScanJob model."""

    scan = ScanField(required=True, many=False, queryset=Scan.objects.all())
    sources = SourceField(many=True, read_only=True)
    scan_type = ValidStringChoiceField(
        read_only=True, choices=ScanTask.SCANTASK_TYPE_CHOICES
    )
    status = ValidStringChoiceField(read_only=True, choices=ScanTask.STATUS_CHOICES)
    status_message = CharField(read_only=True)
    tasks = TaskField(many=True, read_only=True)
    options = ScanOptionsSerializer(read_only=True, many=False)
    report_id = IntegerField(read_only=True)
    start_time = DateTimeField(required=False, read_only=True)
    end_time = DateTimeField(required=False, read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = ScanJob
        fields = [
            "id",
            "scan",
            "sources",
            "scan_type",
            "status",
            "status_message",
            "tasks",
            "options",
            "report_id",
            "start_time",
            "end_time",
        ]

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources
