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

from io import StringIO
import logging
import csv
from rest_framework import renderers
from api.models import FactCollection, Source
from api.common.util import CSVHelper


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class FactCollectionCSVRenderer(renderers.BaseRenderer):
    """Class to render detailed report as CSV."""

    # pylint: disable=too-few-public-methods
    media_type = 'text/csv'
    format = 'csv'

    def render(self,
               fact_collection_dict,
               media_type=None,
               renderer_context=None):
        """Render detailed report as CSV."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals

        report_id = fact_collection_dict.get('id')
        if report_id is None:
            return None

        fact_collection = FactCollection.objects.filter(
            id=report_id).first()
        if fact_collection is None:
            return None

        # Check for a cached copy of csv
        csv_content = fact_collection.csv_content
        if csv_content:
            logger.debug('Using cached csv results for fact collection %d',
                         report_id)
            return csv_content
        logger.debug('No cached csv results for fact collection %d',
                     report_id)

        csv_helper = CSVHelper()
        fact_collection_dict_buffer = StringIO()
        csv_writer = csv.writer(fact_collection_dict_buffer, delimiter=',')

        sources = fact_collection_dict.get('sources')

        csv_writer.writerow(['Report', 'Number Sources'])
        if sources is None:
            csv_writer.writerow([report_id, 0])
            return fact_collection_dict_buffer.getvalue()

        csv_writer.writerow([report_id, len(sources)])
        csv_writer.writerow([])
        csv_writer.writerow([])

        for source in sources:
            source_object = Source.objects.get(pk=source.get('source_id'))
            source_name = source_object.name
            csv_writer.writerow(['Source'])
            csv_writer.writerow(['id', 'name', 'type'])
            csv_writer.writerow([
                source.get('source_id'),
                source_name,
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

                csv_writer.writerow(row)

            csv_writer.writerow([])
            csv_writer.writerow([])

        logger.debug('Caching csv results for fact collection %d',
                     report_id)
        csv_content = fact_collection_dict_buffer.getvalue()
        fact_collection.csv_content = csv_content
        fact_collection.save()
        return csv_content


class ReportCSVRenderer(renderers.BaseRenderer):
    """Class to render Deployment report as CSV."""

    # pylint: disable=too-few-public-methods
    media_type = 'text/csv'
    format = 'csv'

    def render(self,
               report_dict,
               media_type=None,
               renderer_context=None):
        """Render deployment report as CSV."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals

        if not bool(report_dict):
            return None

        csv_helper = CSVHelper()
        report_buffer = StringIO()
        csv_writer = csv.writer(report_buffer, delimiter=',')

        report_id = report_dict.get('report_id')
        systems_list = report_dict.get('report')

        csv_writer.writerow(['Report'])
        csv_writer.writerow([report_id])
        csv_writer.writerow([])
        csv_writer.writerow([])

        if not systems_list:
            return None
        csv_writer.writerow(['Report:'])

        headers = csv_helper.generate_headers(
            systems_list, exclude=set([
                'id', 'report_id', 'metadata']))
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
