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
import os
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.authentication import (TokenAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from api.models import FactCollection
from api.serializers import FactCollectionSerializer
from api.fact.util import (validate_fact_collection_json,
                           get_or_create_fact_collection)
from fingerprinter import pfc_signal

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-many-ancestors


class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """ModelViewSet to publish system facts."""

    if not os.getenv('QPC_DISABLE_AUTHENTICATION', False):
        authentication_classes = (TokenAuthentication, SessionAuthentication)
        permission_classes = (IsAuthenticated,)

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
        fact_collection = get_or_create_fact_collection(request.data)

        # Send signal so fingerprint engine processes raw facts
        try:
            pfc_signal.send(sender=self.__class__,
                            instance=fact_collection)
            # Transition from persisted to complete after processing
            fact_collection.status = FactCollection.FC_STATUS_COMPLETE
            fact_collection.save()
            logger.debug(
                'Fact collection %d successfully processed.',
                fact_collection.id)
        except Exception as error:
            # Transition from persisted to failed after engine failed
            fact_collection.status = FactCollection.FC_STATUS_FAILED
            fact_collection.save()
            logger.error(
                'Fact collection %d failed to be processed.',
                fact_collection.id)
            logger.error('%s:%s', error.__class__.__name__, error)
            raise error

        # Prepare REST response body
        serializer = self.get_serializer(fact_collection)
        result = serializer.data
        return Response(result, status=status.HTTP_201_CREATED)
