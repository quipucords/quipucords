#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Module for serializing all model object for database storage."""
from rest_framework.serializers import CharField, ChoiceField

from api.common.serializer import CustomJSONField, NotEmptySerializer
from api.models import (
    JobInspectionResult,
    RawFact,
    SystemInspectionResult,
    TaskInspectionResult,
)


class RawFactSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    value = CustomJSONField(required=True)

    class Meta:
        """Metadata for serialzer."""

        model = RawFact
        fields = ["name", "value"]
        qpc_allow_empty_fields = []


class SystemInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    status = ChoiceField(
        required=True, choices=SystemInspectionResult.CONN_STATUS_CHOICES
    )

    class Meta:
        """Metadata for serialzer."""

        model = SystemInspectionResult
        fields = ["name", "status", "source", "facts"]
        qpc_allow_empty_fields = ["facts", "source"]


class TaskInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the TaskInspectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = TaskInspectionResult
        fields = ["source", "systems"]
        qpc_allow_empty_fields = ["source", "systems"]


class JobInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the JobInspectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = JobInspectionResult
        fields = ["task_results"]
        qpc_allow_empty_fields = ["task_results"]
