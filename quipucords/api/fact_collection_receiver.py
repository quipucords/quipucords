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

"""Models to capture system facts."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from fingerprinter import Engine
from api.serializers import FingerprintSerializer, FactCollectionSerializer
from api.models import FactCollection

ENGINE = Engine()
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@receiver(post_save, sender=FactCollection)
def process_fact_collection(sender, instance, **kwargs):
    """Process facts using engine and convert to fingerprints

    :param sender: Class that was saved
    :param instance: FactCollection that was saved
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument

    # Convert to python dictionary
    fact_collection = FactCollectionSerializer(instance).data

    # Extract facts and collection id
    fact_collection_id = fact_collection['id']
    facts = fact_collection['facts']

    # Invoke ENGINE to create fingerprints from facts
    fingerprints_list = ENGINE.process_facts(
        fact_collection_id, facts)

    for fingerprint_dict in fingerprints_list:
        serializer = FingerprintSerializer(data=fingerprint_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.error('%s could not persist fingerprint. Fact: %s',
                         __name__, fingerprint_dict)
            logger.error('Errors: %s', serializer.errors)
