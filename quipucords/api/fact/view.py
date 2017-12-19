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
import json
from django.conf import settings
from django.utils.translation import ugettext as _
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from api.models import FactCollection
from api.serializers import FactCollectionSerializer
from api.signals.fact_collection_receiver import pfc_signal
import api.messages as messages


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
        if not request.data.get('sources'):
           raise ValidationError(_(messages.FC_REQUIRED_ATTRIBUTE % 'sources'))

        # Remove to make serializer happy since its not part of the model
        sources = request.data.pop('sources')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #validate sources
        serializer.validate_sources(sources)

        # Create fact collection
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Find instance for signal
        fact_collection = FactCollection.objects.get(pk=serializer.data['id'])

        # Add sources back to request data
        request.data['sources'] = sources
        result = serializer.data
        result['sources'] = sources

        # Save raw facts and update fact collection
        fact_collection.path = save_raw_facts(
            fact_collection.id, request.data)
        fact_collection.save()

        pfc_signal.send(sender=self.__class__,
                        instance=fact_collection,
                        facts=request.data)
        return Response(result, status=status.HTTP_201_CREATED,
                        headers=headers)

def save_raw_facts(fc_id, data):
    """Write raw facts to json file."""
    if not os.path.exists(settings.FACTS_DIR):
        os.makedirs(settings.FACTS_DIR)

    file_path = '%s/%d.json' % (settings.FACTS_DIR, fc_id)
    with open(file_path, 'w') as raw_fact_file:
        json.dump(data, raw_fact_file)

    return file_path
