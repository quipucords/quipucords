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
from api.models import SystemFingerprint
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import (DocType,
                               Date,
                               Keyword,
                               Index,
                               Integer,
                               Boolean)
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
        fact_collection=instance.id,
        connection_host=instance.connection_host,
        connection_port=instance.connection_port,
        connection_uuid=instance.connection_uuid,
        cpu_count=instance.cpu_count,
        cpu_core_per_socket=instance.cpu_core_per_socket,
        cpu_siblings=instance.cpu_siblings,
        cpu_hyperthreading=instance.cpu_hyperthreading,
        cpu_socket_count=instance.cpu_socket_count,
        cpu_core_count=instance.cpu_core_count,
        system_creation_date=instance.system_creation_date,
        infrastructure_type=instance.infrastructure_type,
        os_name=instance.os_name,
        os_version=instance.os_version,
        os_release=instance.os_release,
        virtualized_is_guest=instance.virtualized_is_guest,
        virtualized_type=instance.virtualized_type,
        virtualized_num_guests=instance.virtualized_num_guests,
        virtualized_num_running_guests=instance.virtualized_num_running_guests,
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

    connection_host = Keyword()
    connection_port = Integer()
    connection_uuid = Keyword()

    cpu_count = Integer()
    cpu_core_per_socket = Integer()
    cpu_siblings = Integer()
    cpu_hyperthreading = Boolean()
    cpu_socket_count = Integer()
    cpu_core_count = Integer()

    system_creation_date = Date()
    infrastructure_type = Keyword()

    virtualized_is_guest = Boolean()
    virtualized_type = Keyword()
    virtualized_num_guests = Integer()
    virtualized_num_running_guests = Integer()

    timestamp = Date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = Index(settings.ES_CONFIGURATION['fingerprint_index_name'])
        if not self.index.exists():
            self.index.create()

    def __str__(self):
        return '{' + \
            'fact_collection_id:{}, '\
            'connection_host:{}, '\
            'connection_port:{}, '\
            'connection_uuid:{}, '\
            'cpu_count:{}, '\
            'cpu_core_per_socket:{}, '\
            'cpu_siblings:{}, '\
            'cpu_hyperthreading:{}, '\
            'cpu_socket_count:{}, '\
            'cpu_core_count:{}, '\
            'system_creation_date:{}, '\
            'infrastructure_type:{}, '\
            'os_name:{},, '\
            'os_version:{},, '\
            'os_release:{},, '\
            'virtualized_is_guest:{}, '\
            'virtualized_type:{}, '\
            'virtualized_num_guests:{}, '\
            'virtualized_num_running_guests:{}, '\
            'timestamp:{}'\
            .format(self.fact_collection_id,
                    self.connection_host,
                    self.connection_port,
                    self.connection_uuid,
                    self.cpu_count,
                    self.cpu_core_per_socket,
                    self.cpu_siblings,
                    self.cpu_hyperthreading,
                    self.cpu_socket_count,
                    self.cpu_core_count,
                    self.system_creation_date,
                    self.infrastructure_type,
                    self.os_name,
                    self.os_version,
                    self.os_release,
                    self.virtualized_is_guest,
                    self.virtualized_type,
                    self.virtualized_num_guests,
                    self.virtualized_num_running_guests,
                    str(self.timestamp)) + '}'

    class Meta:
        """FingerPrintIndex Meta class."""
        # pylint: disable=too-few-public-methods
        index = 'fingerprints_index'
        doc_type = 'fingerprint'
