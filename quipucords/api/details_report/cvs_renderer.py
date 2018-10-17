#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""CSV renderer for reports."""

import csv
import logging
from io import StringIO

from api.common.util import CSVHelper
from api.models import (DetailsReport)

from rest_framework import renderers


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

NETWORK_DETECTION_KEY = 'detection-network'
VCENTER_DETECTION_KEY = 'detection-vcenter'
SATELLITE_DETECTION_KEY = 'detection-satellite'
SOURCES_KEY = 'sources'


def sanitize_row(row):
    """Replace commas in fact values to prevent false csv parsing."""
    return [fact.replace(',', ';')
            if isinstance(fact, str) else fact for fact in row]


class DetailsCSVRenderer(renderers.BaseRenderer):
    """Class to render detailed report as CSV."""

    # pylint: disable=too-few-public-methods
    media_type = 'text/csv'
    format = 'csv'

    def render(self,
               details_report_dict,
               media_type=None,
               renderer_context=None):
        """Render detailed report as CSV."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals
        report_id = details_report_dict.get('report_id')
        if report_id is None:
            return None

        details_report = DetailsReport.objects.filter(
            report_id=report_id).first()
        if details_report is None:
            return None

        # Check for a cached copy of csv
        cached_csv = details_report.cached_csv
        if cached_csv:
            logger.info('Using cached csv results for details report %d',
                        report_id)
            return cached_csv
        logger.info('No cached csv results for details report %d',
                    report_id)

        csv_helper = CSVHelper()
        details_report_csv_buffer = StringIO()
        csv_writer = csv.writer(details_report_csv_buffer, delimiter=',')

        sources = details_report_dict.get('sources')

        csv_writer.writerow(['Report', 'Number Sources'])
        if sources is None:
            csv_writer.writerow([report_id, 0])
            return details_report_csv_buffer.getvalue()

        csv_writer.writerow([report_id, len(sources)])
        csv_writer.writerow([])
        csv_writer.writerow([])

        for source in sources:
            csv_writer.writerow(['Source'])
            csv_writer.writerow(
                ['Server Identifier',
                 'Source Name',
                 'Source Type'])
            csv_writer.writerow([
                source.get('server_id'),
                source.get('source_name'),
                source.get('source_type')])
            csv_writer.writerow(['Facts'])
            fact_list = source.get('facts')
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

        logger.info('Caching csv results for details report %d',
                    report_id)
        cached_csv = details_report_csv_buffer.getvalue()
        details_report.cached_csv = cached_csv
        details_report.save()

        return cached_csv
