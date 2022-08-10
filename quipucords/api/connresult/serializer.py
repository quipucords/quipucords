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


from rest_framework.serializers import CharField, ChoiceField

# pylint: disable=wrong-import-order
from api.common.serializer import NotEmptySerializer  # noqa
from api.models import JobConnectionResult, SystemConnectionResult, TaskConnectionResult


class SystemConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the SystemConnectionResult model."""

    name = CharField(required=True)
    status = ChoiceField(
        required=True, choices=SystemConnectionResult.CONN_STATUS_CHOICES
    )

    class Meta:
        """Metadata for serialzer."""

        model = SystemConnectionResult
        fields = ["name", "status", "source", "credential"]
        qpc_allow_empty_fields = ["value", "source"]


class TaskConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the TaskConnectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = TaskConnectionResult
        fields = ["source", "systems"]
        qpc_allow_empty_fields = ["source", "systems"]


class JobConnectionResultSerializer(NotEmptySerializer):
    """Serializer for the JobConnectionResult model."""

    class Meta:
        """Metadata for serialzer."""

        model = JobConnectionResult
        fields = ["task_results"]
        qpc_allow_empty_fields = ["task_results"]
