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
from api.models import (InspectionResults, InspectionResult,
                        SystemInspectionResult, RawFact)
from api.common.serializer import NotEmptySerializer


class RawFactSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    value = CharField(required=True)

    class Meta:
        """Metadata for serialzer."""

        model = RawFact
        fields = ['name', 'value']
        qpc_allow_empty_fields = []


class SystemInspectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemInspectionResult model."""

    name = CharField(required=True, max_length=1024)
    status = ChoiceField(
        required=True, choices=SystemInspectionResult.CONN_STATUS_CHOICES)

    class Meta:
        """Metadata for serialzer."""

        model = SystemInspectionResult
        fields = ['name', 'status', 'facts']
        qpc_allow_empty_fields = ['facts']


class InspectionResultSerializer(NotEmptySerializer):
    """Serializer for the InspectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = InspectionResult
        fields = ['source', 'systems']
        qpc_allow_empty_fields = ['source', 'systems']


class InspectionResultsSerializer(NotEmptySerializer):
    """Serializer for the InspectionResults model."""

    class Meta:
        """Metadata for serialzer."""

        model = InspectionResults
        fields = ['scan_job', 'results']
        qpc_allow_empty_fields = ['results']
