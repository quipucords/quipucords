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

"""Viewset for system reports."""
import logging
import os
from django.utils.translation import ugettext as _
from django.db.models import Count
from django.core.exceptions import FieldError
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import (TokenAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from api.models import SystemFingerprint
from api.serializers import FingerprintSerializer
import api.messages as messages


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportListView(APIView):
    """List all system reports."""

    authentication_enabled = os.getenv('QPC_DISABLE_AUTHENTICATION') != 'True'
    if authentication_enabled:
        authentication_classes = (TokenAuthentication, SessionAuthentication)
        permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Lookup and return all system reports."""
        self.validate_filters(request.query_params)

        fact_collection_id = request.query_params.get(
            'fact_collection_id', None)

        if fact_collection_id is None:
            collection_report_list = []
            # Find all distinct fact_collection_ids
            fact_collection_value_set = SystemFingerprint.objects.all().values(
                'fact_collection_id').distinct()

            # For each id, build a report and add to results array
            for fact_collection_value in fact_collection_value_set:
                fact_collection_id = fact_collection_value[
                    'fact_collection_id']
                report = self.build_report(fact_collection_id,
                                           request.query_params)
                if report is not None:
                    collection_report_list.append(report)
                else:
                    logger.error(
                        'System Fingerprint with fact_collection_id ' +
                        '%s no longer exists',
                        fact_collection_id)
            return Response(collection_report_list)
        else:
            report = self.build_report(fact_collection_id,
                                       request.query_params)
            if report is not None:
                return Response(report)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def validate_filters(filters):
        """Check the combination of filters are allowed.

        :param filters: report filters to checks
        :raises: Raises validation error if the combination of
        filters is not allowed.
        """
        filter_count = len(filters.keys())
        fc_found = filters.get('fact_collection_id', None)
        group_count_found = filters.get('group_count', None)
        if group_count_found is not None:
            if fc_found is not None and filter_count > 2:
                error = {
                    'query_params': [_(messages.REPORT_GROUP_COUNT_FILTER)]
                }
                raise ValidationError(error)
            elif fc_found is None and filter_count > 1:
                error = {
                    'query_params': [_(messages.REPORT_GROUP_COUNT_FILTER)]
                }
                raise ValidationError(error)

    @staticmethod
    def build_grouped_report(fact_collection_id, fingerprints, group):
        """Create a count report based on the fingerprints and the group.

        :param fact_collection_id: the identifer for the fact collection
        :param fingerprints: The system fingerprints used in the group count
        :param group: the field to group and count on
        :returns: json report data
        :raises: Raises validation error group_count on non-existent field.
        """
        try:
            # Group by field and count
            counts_by_group = fingerprints.values(
                group).annotate(total=Count(group))
        except FieldError:
            msg = _(messages.REPORT_GROUP_COUNT_FIELD % (group))
            error = {
                'query_params': [msg]
            }
            raise ValidationError(error)

        if len(counts_by_group) is 0:
            return None

        # Build response dictionary
        report = {'fact_collection_id': fact_collection_id,
                  'report': []}
        for group_count in counts_by_group:
            report['report'].append(
                {
                    group: group_count[group],
                    'count': group_count['total']
                }
            )
        return report

    @staticmethod
    def filter_keys(filters):
        """Get the values to supply based on the filters.

        :param fiters: filters for the report
        :returns: list of keys to display in report
        """
        filter_list = []
        filters_clone = filters.copy()
        filters_clone.pop('fact_collection_id', None)
        filters_clone.pop('group_count', None)
        for filter_key, filter_value in filters_clone.items():
            if (isinstance(filter_value, str) and
                    filter_value.lower() == 'true'):
                filter_list.append(filter_key)
        return set(filter_list)

    def build_report(self, fact_collection_id, filters):
        """Lookup system report by fact_collection_id.

        :param fact_collection_id: the identifer for the fact collection
        :param fiters: filters for the report
        :returns: json report data
        """
        # We want aggregate counts on the fact collection groups
        # Find all fingerprints with this fact_collection_id
        fingerprints = SystemFingerprint.objects.filter(
            fact_collection_id__id=fact_collection_id)

        if len(fingerprints) is 0:
            return None

        group = filters.get('group_count', None)
        if group is not None:
            return self.build_grouped_report(fact_collection_id,
                                             fingerprints,
                                             group)
        # Build response dictionary
        report = {'fact_collection_id': fact_collection_id,
                  'report': []}
        filter_keys = self.filter_keys(filters)
        for fingerprint in fingerprints:
            serializer = FingerprintSerializer(fingerprint)
            if filter_keys == set():
                report['report'].append(serializer.data)
            else:
                filtered_data = {}
                for key in filter_keys:
                    visible_data = serializer.data.get(key, None)
                    filtered_data[key] = visible_data
                report['report'].append(filtered_data)
        return report
