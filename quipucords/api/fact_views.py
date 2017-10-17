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

"""Viewset for system facts models"""

from rest_framework import viewsets, mixins
from api.fact_model import FactCollection
from api.fact_serializer import FactCollectionSerializer
from api.fingerprint_serializer import FingerprintSerializer
from fingerprinter import Engine


# pylint: disable=too-many-ancestors
class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """
    ModelViewSet to publish system facts.
    """
    queryset = FactCollection.objects.all()
    serializer_class = FactCollectionSerializer

    def __init__(self, *args, **kwargs):
        super(FactViewSet, self).__init__(*args, **kwargs)
        self.engine = Engine()

    def create(self, request, *args, **kwargs):
        """
        Method to publish system facts, process facts,
        and persist resulting fingerprints
        """

        response = super().create(request)
        self.persist_fingerprints(response.data)
        return response

    def persist_fingerprints(self, data):
        """
        Method to process facts and persist
        resulting fingerprints
        """

        fact_collection_id = data['id']
        facts = data['facts']
        fingerprints_list = self.engine.process_facts(
            fact_collection_id, facts)

        fingerprints = []
        for fingerprint_dict in fingerprints_list:
            serializer = FingerprintSerializer(data=fingerprint_dict)
            if serializer.is_valid():
                serializer.save()
            fingerprint = serializer.save()
            fingerprints.append(fingerprint)
        return fingerprints
