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

import logging
from rest_framework import viewsets, mixins
from api.models import FactCollection
from api.serializers import FactCollectionSerializer


# pylint: disable=too-many-ancestors
class FactViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """
    ModelViewSet to publish system facts.
    """

    # Get an instance of a logger
    logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

    queryset = FactCollection.objects.all()
    serializer_class = FactCollectionSerializer
