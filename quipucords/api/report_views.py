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

"""Viewset for system reports"""
import logging
from django.db.models import Count
from api.fingerprint_model import SystemFingerprint
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportListView(APIView):
    """List all system reports."""

    def get(self, request):
        """Lookup and return all system reports."""
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
                report = self.build_report(fact_collection_id)
                if report is not None:
                    collection_report_list.append(report)
                else:
                    logger.error(
                        'System Fingerprint with fact_collection_id ' +
                        '%s no longer exists',
                        fact_collection_id)
            return Response(collection_report_list)
        else:
            report = self.build_report(fact_collection_id)
            if report is not None:
                return Response(report)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def build_report(fact_collection_id):
        """Lookup system report by fact_collection_id."""
        # We want aggregate counts on the fact collection groups
        # Find all fingerprints with this fact_collection_id

        fc_fingerprints = SystemFingerprint.objects.filter(
            fact_collection_id__id=fact_collection_id)

        # Group by os_release and count
        counts_by_os = fc_fingerprints.values(
            'os_release').annotate(total=Count('os_release'))

        if len(counts_by_os) is 0:
            return None

        # Build response dictionary
        report = {'fact_collection_id': fact_collection_id,
                  'report': []}
        for os_count in counts_by_os:
            report['report'].append(
                {
                    'os_release': os_count['os_release'],
                    'count': os_count['total']
                }
            )

        return report
