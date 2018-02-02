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
"""CSV renderer for facts models."""

from io import StringIO
import logging
import csv
from rest_framework import renderers
from api.common.util import CSVHelper


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportCSVRenderer(renderers.BaseRenderer):
    """Class to render FactCollection as CSV."""

    # pylint: disable=too-few-public-methods
    media_type = 'text/csv'
    format = 'csv'

    def render(self,
               report_dict,
               media_type=None,
               renderer_context=None):
        """Render FactCollection as CSV."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals

        if not bool(report_dict):
            return None

        csv_helper = CSVHelper()
        report_buffer = StringIO()
        csv_writer = csv.writer(report_buffer, delimiter=',')

        fact_collection_id = report_dict.get('fact_collection_id')
        systems_list = report_dict.get('report')

        csv_writer.writerow(['Fact Collection'])
        csv_writer.writerow([fact_collection_id])
        csv_writer.writerow([])
        csv_writer.writerow([])

        if not systems_list:
            return None
        csv_writer.writerow(['Report:'])

        headers = csv_helper.generate_headers(
            systems_list, exclude=set([
                'id', 'fact_collection_id', 'metadata']))
        csv_writer.writerow(headers)
        for system in systems_list:
            row = []
            for header in headers:
                fact_value = system.get(header)
                row.append(csv_helper.serialize_value(header, fact_value))
            csv_writer.writerow(row)

        csv_writer.writerow([])

        csv_content = report_buffer.getvalue()
        return csv_content
