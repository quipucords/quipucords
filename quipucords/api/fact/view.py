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
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from api.models import FactCollection
from api.serializers import FactCollectionSerializer
from api.fact.util import (validate_fact_collection_json,
                           create_fact_collection,
                           SOURCES_KEY,
                           VALID_SOURCES_KEY)
from fingerprinter import pfc_signal


# pylint: disable=too-many-ancestors
class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """ModelViewSet to publish system facts."""

    # Get an instance of a logger
    logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

    queryset = FactCollection.objects.all()
    serializer_class = FactCollectionSerializer

    def create(self, request, *args, **kwargs):
        """Create a fact collection."""
        # Validate incoming request body
        has_errors, validation_result = validate_fact_collection_json(
            request.data)
        if has_errors:
            return Response(validation_result,
                            status=status.HTTP_400_BAD_REQUEST)

        # Create FC model and save data to JSON file
        fact_collection = create_fact_collection(request.data)

        # Prepare REST response body
        serializer = self.get_serializer(fact_collection)
        result = serializer.data
        result[SOURCES_KEY] = validation_result[VALID_SOURCES_KEY]

        # Send signal so fingerprint engine processes raw facts
        pfc_signal.send(sender=self.__class__,
                        instance=fact_collection)
        return Response(result, status=status.HTTP_201_CREATED)
