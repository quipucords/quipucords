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

"""Viewset for system facts models."""

import logging
from django.utils.translation import ugettext as _
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
import api.messages as messages
from api.models import FactCollection, Source
from api.serializers import FactCollectionSerializer
from api.signals.fact_collection_receiver import pfc_signal
from api.fact.raw_fact_util import write_raw_facts


# pylint: disable=too-many-ancestors
class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """ModelViewSet to publish system facts."""

    # Get an instance of a logger
    logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

    queryset = FactCollection.objects.all()
    serializer_class = FactCollectionSerializer

    INVALID_SOURCES = 'invalid_sources'
    VALID_SOURCES = 'valid_sources'

    # JSON attribute constants
    SOURCES_ATTR = 'sources'
    SOURCE_ID_ATTR = 'source_id'
    SOURCE_TYPE_ATTR = 'source_type'
    FACTS_ATTR = 'facts'

    def create(self, request, *args, **kwargs):
        """Create a fact collection."""
        if not request.data.get(self.SOURCES_ATTR):
            return Response({self.SOURCES_ATTR:
                             _(messages.FC_REQUIRED_ATTRIBUTE)},
                            status=status.HTTP_400_BAD_REQUEST)

        # Remove to make serializer happy since its not part of the model
        sources = request.data.get(self.SOURCES_ATTR)

        # validate sources
        validation_results = self.validate_sources(sources)
        if validation_results.get(self.INVALID_SOURCES):
            # Errors so return 400
            return Response(validation_results,
                            status=status.HTTP_400_BAD_REQUEST)

        # Create fact collection
        fact_collection = FactCollection()
        fact_collection.save()

        # Save raw facts and update fact collection
        fact_collection.path = write_raw_facts(
            fact_collection.id, request.data)
        fact_collection.save()

        # Add sources back (not in model so manual)
        serializer = self.get_serializer(fact_collection)
        result = serializer.data
        result[self.SOURCES_ATTR] = sources

        pfc_signal.send(sender=self.__class__,
                        instance=fact_collection)
        return Response(result, status=status.HTTP_201_CREATED)

    def validate_sources(self, sources):
        """Validate sources field."""
        valid_sources = []
        invalid_sources = []
        for source in sources:
            error = self.validate_source(source)
            if error:
                invalid_sources.append(error)
            else:
                valid_sources.append(source)

        return {self.VALID_SOURCES: valid_sources,
                self.INVALID_SOURCES: invalid_sources}

    def validate_source(self, source_json):
        """Validate source fields."""
        invalid_field_obj = {}
        source_id = source_json.get(self.SOURCE_ID_ATTR)
        has_error = False
        if not source_id:
            has_error = True
            invalid_field_obj[self.SOURCE_ID_ATTR] = _(
                messages.FC_REQUIRED_ATTRIBUTE)

        if not has_error and not isinstance(source_id, int):
            has_error = True
            invalid_field_obj[self.SOURCE_ID_ATTR] = _(
                messages.FC_SOURCE_ID_NOT_INT)

        if not has_error:
            source = Source.objects.filter(pk=source_id).first()
            if not source:
                has_error = True
                invalid_field_obj[self.SOURCE_ID_ATTR] = _(
                    messages.FC_SOURCE_NOT_FOUND % source_id)

        source_type = source_json.get(self.SOURCE_TYPE_ATTR)
        if not source_type:
            has_error = True
            invalid_field_obj[self.SOURCE_TYPE_ATTR] = _(
                messages.FC_REQUIRED_ATTRIBUTE)

        if not has_error and not \
                [valid_type for valid_type in Source.SOURCE_TYPE_CHOICES
                 if valid_type[0] == source_type]:
            has_error = True
            valid_choices = ', '.join(
                [valid_type[0] for valid_type in Source.SOURCE_TYPE_CHOICES])
            invalid_field_obj[self.SOURCE_TYPE_ATTR] = _(
                messages.FC_MUST_BE_ONE_OF % valid_choices)

        facts = source_json.get(self.FACTS_ATTR)
        if not facts:
            has_error = True
            invalid_field_obj[self.FACTS_ATTR] = _(
                messages.FC_REQUIRED_ATTRIBUTE)

        if has_error:
            error_json = {}
            error_json['source'] = source_json
            error_json['errors'] = invalid_field_obj
            return error_json
        return None
