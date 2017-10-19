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

import time
import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.fingerprint_model import SystemFingerprint
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, Date, Keyword, Index
from elasticsearch.exceptions import RequestError

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

HOSTS = settings.ES_HOSTS.split(',')
connections.configure(default={'hosts': HOSTS})
ES_CONNECTION = connections.get_connection()
logger.debug('ES Connection Status:\n%s',
             ES_CONNECTION.cluster.health())


@receiver(post_save, sender=SystemFingerprint)
def index_fingerprint(sender, instance, **kwargs):
    """Process facts using engine and convert to fingerprints

    :param sender: Class that was saved
    :param instance: SystemFingerprint that was saved
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument
    es_fingerprint = FingerPrintIndex(
        fact_collection_id=instance.id, os_name=instance.os_name,
        os_release=instance.os_release, os_version=instance.os_version,
        timestamp=int(round(time.time() * 1000)))

    try:
        es_fingerprint.save()
        logger.debug('%s persisted fingerprint in ES: %s',
                     __name__, es_fingerprint)
    except RequestError as error:
        logger.error('%s failed to persist fingerprint: %s\n%s',
                     __name__, es_fingerprint, error)


class FingerPrintIndex(DocType):
    """Represents the elasticsearch fingerprint index"""
    fact_collection_id = Keyword()
    os_name = Keyword()
    os_release = Keyword()
    os_version = Keyword()
    timestamp = Date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = Index(settings.ES_CONFIGURATION['fingerprint_index_name'])
        if not self.index.exists():
            self.index.create()

    def __str__(self):
        return '{' + 'id:{}, fact_collection:{}, ' \
            'os_name:{}, os_release:{}, '\
            'os_version:{}' \
            .format(
                self.fact_collection_id,
                self.os_name,
                self.os_release,
                self.os_version,
                str(self.timestamp) + '}')

    class Meta:
        """FingerPrintIndex Meta class."""
        # pylint: disable=too-few-public-methods
        index = 'fingerprints_index'
        doc_type = 'fingerprint'
