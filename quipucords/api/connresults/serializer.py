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
from api.models import (ConnectionResults, ConnectionResult,
                        SystemConnectionResult)
from api.common.serializer import NotEmptySerializer


class SystemConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemConnectionResult model."""

    name = CharField(required=True, max_length=1024)
    status = ChoiceField(
        required=True, choices=SystemConnectionResult.CONN_STATUS_CHOICES)

    class Meta:
        """Metadata for serialzer."""

        model = SystemConnectionResult
        fields = ['name', 'credential', 'status']
        qpc_allow_empty_fields = ['value']


class ConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the ConnectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = ConnectionResult
        fields = ['source', 'systems']
        qpc_allow_empty_fields = ['source', 'systems']


class ConnectionResultsSerializer(NotEmptySerializer):
    """Serializer for the ConnectionResults model."""

    class Meta:
        """Metadata for serialzer."""

        model = ConnectionResults
        fields = ['scan_job', 'results']
        qpc_allow_empty_fields = ['results']
