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
import django.dispatch
from fingerprinter import Engine
from api.fact.raw_fact_util import read_raw_facts
from api.serializers import FingerprintSerializer

ENGINE = Engine()
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def process_fact_collection(sender, instance, **kwargs):
    """Restart a scan.

    :param sender: Class that was saved
    :param instance: FactCollection that was saved
    :param facts: dict of raw facts
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument
    raw_facts = read_raw_facts(instance.id)

    # Invoke ENGINE to create fingerprints from facts
    fingerprints_list = ENGINE.process_sources(raw_facts)

    for fingerprint_dict in fingerprints_list:
        serializer = FingerprintSerializer(data=fingerprint_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.error('%s could not persist fingerprint. SystemFacts: %s',
                         __name__, fingerprint_dict)
            logger.error('Errors: %s', serializer.errors)


# pylint: disable=C0103
pfc_signal = django.dispatch.Signal(providing_args=[
    'instance'])

pfc_signal.connect(process_fact_collection)
