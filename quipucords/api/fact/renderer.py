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
from api.models import FactCollection, Source


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class FactCollectionCSVRenderer(renderers.BaseRenderer):
    """Class to render FactCollection as CSV."""

    media_type = 'text/csv'
    format = 'csv'

    def render(self,
               fact_collection_dict,
               media_type=None,
               renderer_context=None):
        """Render FactCollection as CSV."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals

        fact_collection_id = fact_collection_dict.get('id')
        if fact_collection_id is None:
            return None

        fact_collection = FactCollection.objects.filter(
            id=fact_collection_id).first()
        if fact_collection is None:
            return None

        # Check for a cached copy of csv
        csv_content = fact_collection.csv_content
        if csv_content:
            logger.debug('Using cached csv results for fact collection %d',
                         fact_collection_id)
            return csv_content
        logger.debug('No cached csv results for fact collection %d',
                     fact_collection_id)

        fact_collection_dict_buffer = StringIO()
        csv_writer = csv.writer(fact_collection_dict_buffer, delimiter=',')

        sources = fact_collection_dict.get('sources')

        csv_writer.writerow(['Fact Collection', 'Number Sources'])
        if sources is None:
            csv_writer.writerow([fact_collection_id, 0])
            return fact_collection_dict_buffer.getvalue()

        csv_writer.writerow([fact_collection_id, len(sources)])
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
            headers = self.generate_headers(fact_list)
            csv_writer.writerow(headers)

            for fact in fact_list:
                row = []
                for header in headers:
                    fact_value = fact.get(header)
                    row.append(self.serialize_value(header, fact_value))

                csv_writer.writerow(row)

            csv_writer.writerow([])
            csv_writer.writerow([])

        logger.debug('Caching csv results for fact collection %d',
                     fact_collection_id)
        csv_content = fact_collection_dict_buffer.getvalue()
        fact_collection.csv_content = csv_content
        fact_collection.save()
        return csv_content

    def serialize_value(self, header, fact_value):
        """Serialize a fact value to a CSV value."""
        if isinstance(fact_value, dict):
            return self.serialize_dict(header, fact_value)
        elif isinstance(fact_value, list):
            return self.serialize_list(header, fact_value)
        return fact_value

    def serialize_list(self, header, fact_list):
        """Serialize a list to a CSV value."""
        # Return empty string for empty list
        if not bool(fact_list):
            return ''

        result = '['
        value_string = '%s;'
        for item in fact_list:
            if isinstance(item, list):
                result += value_string % self.serialize_list(header, item)
            elif isinstance(item, dict):
                result += value_string % self.serialize_dict(header, item)
            else:
                result += value_string % item
        result = result[:-1] + ']'
        return result

    def serialize_dict(self, header, fact_dict):
        """Serialize a dict to a CSV value."""
        # Return empty string for empty dict
        if not bool(fact_dict):
            return ''
        if fact_dict.get('rc') is not None:
            logger.error(
                'Fact appears to be raw ansible output. %s=%s',
                header, fact_dict)
            return 'ERROR_SEE_LOGS'

        result = '{'
        value_string = '%s:%s;'
        for key, value in fact_dict.items():
            if isinstance(value, list):
                result += value_string % (key,
                                          self.serialize_list(header, value))
            elif isinstance(value, dict):
                result += value_string % (key,
                                          self.serialize_dict(header, value))
            else:
                result += value_string % (key, value)
        result = result[:-1] + '}'
        return result

    @staticmethod
    def generate_headers(fact_list):
        """Generate column headers from fact list."""
        headers = set()
        for fact in fact_list:
            for fact_key in fact.keys():
                headers.add(fact_key)

        return sorted(list(headers))
