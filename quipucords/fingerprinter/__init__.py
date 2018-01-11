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

"""Fingerprint engine ingests raw facts and produces system finger prints."""

import logging
from datetime import datetime
import django.dispatch
from api.fact.util import read_raw_facts
from api.models import FactCollection
from api.serializers import FingerprintSerializer

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=unused-argument


def process_fact_collection(sender, instance, **kwargs):
    """Process the fact collection.

    :param sender: Class that was saved
    :param instance: FactCollection that was saved
    :param facts: dict of raw facts
    :param kwargs: Other args
    :returns: None
    """
    raw_facts = read_raw_facts(instance.id)

    # Invoke ENGINE to create fingerprints from facts
    fingerprints_list = FINGERPRINT_ENGINE.process_sources(instance, raw_facts)
    fingerprints_list = remove_duplicate_systems(
        fingerprints_list, ['subscription_manager_id', 'bios_uuid'])

    for fingerprint_dict in fingerprints_list:
        serializer = FingerprintSerializer(data=fingerprint_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.error('%s could not persist fingerprint. SystemFacts: %s',
                         __name__, fingerprint_dict)
            logger.error('Errors: %s', serializer.errors)

    # Mark completed because engine has process raw facts
    instance.status = FactCollection.FC_STATUS_COMPLETE
    instance.save()


def remove_duplicate_systems(initial_systems, identification_keys):
    """Remove duplicate systems from list.

    Systems who have the same value for any one of the identification
    keys are considered duplicates.
    :param initial_systems: The systems to deduplicate. Passed as
    list of dict containing system facts
    :param identification_keys: list of keys used to identify a system
    :returns: A list of unique systems determined the identification_keys
    """
    systems = initial_systems[:]
    for identification_key in identification_keys:
        systems_by_id_key = {}
        systems_without_key = []
        for system in systems:
            system_id_key = system.get(identification_key)
            if system_id_key:
                # System has key so add/overwrite system with key
                systems_by_id_key[system_id_key] = system
            else:
                # Key is not a system fact, so add to list
                systems_without_key.append(system)
        # merge systems_without_key with unique set of systems
        systems = systems_without_key + list(systems_by_id_key.values())
    return systems


class Engine():
    """Engine that produces fingerprints from facts."""

    # pylint: disable=no-self-use,too-many-branches,too-many-statements
    # pylint: disable=too-few-public-methods

    def process_sources(self, fact_collection, raw_facts):
        """Process facts and convert to fingerprints.

        :param fact_collection: FactCollection associated with
        raw facts
        :param raw_facts: Collected raw facts for all sources
        :returns: list of fingerprints for all systems (all scans)
        """
        all_fingerprints = []
        for source in raw_facts['sources']:
            source_fingerprints = self._process_facts(
                raw_facts['fact_collection_id'],
                source['source_id'],
                source['facts'])
            all_fingerprints = all_fingerprints + source_fingerprints
        logger.debug('FactCollection %d produced %d fingerprints',
                     fact_collection.id, len(all_fingerprints))
        return all_fingerprints

    def _process_facts(self, fact_collection_id, source_id, facts):
        """Process facts and convert to fingerprints.

        :param fact_collection_id: id of fact collection
        associated with facts
        :param source_id: id of source associated with facts
        :param facts: facts to process
        :returns: fingerprints produced from facts
        """
        fingerprints = []
        for fact in facts:
            fingerprint = self._process_fact(fact)
            fingerprint['fact_collection_id'] = fact_collection_id
            fingerprint['source_id'] = source_id
            fingerprints.append(fingerprint)
        return fingerprints

    def _process_fact(self, fact):
        """Process a fact and convert to a fingerprint.

        associated with facts
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        # Set fact collection id
        fingerprint = {}

        # Set OS information
        if fact.get('etc_release_name'):
            fingerprint['os_name'] = fact['etc_release_name']

        if fact.get('etc_release_version'):
            fingerprint['os_version'] = fact['etc_release_version']

        if fact.get('etc_release_release'):
            fingerprint['os_release'] = fact['etc_release_release']

        # Set bios UUID
        if fact.get('dmi_system_uuid'):
            fingerprint['bios_uuid'] = fact['dmi_system_uuid']

        # Set subscription manager id
        if fact.get('subman_virt_uuid'):
            fingerprint['subscription_manager_id'] = fact['subman_virt_uuid']

        # Set connection information
        if fact.get('connection_uuid'):
            fingerprint['connection_uuid'] = fact['connection_uuid']

        if fact.get('connection_host'):
            fingerprint['connection_host'] = fact['connection_host']

        if fact.get('connection_port'):
            fingerprint['connection_port'] = fact['connection_port']

        # Set CPU facts
        if fact.get('cpu_count'):
            fingerprint['cpu_count'] = fact['cpu_count']

        if fact.get('cpu_core_per_socket'):
            fingerprint['cpu_core_per_socket'] = fact['cpu_core_per_socket']

        if fact.get('cpu_siblings'):
            fingerprint['cpu_siblings'] = fact['cpu_siblings']

        if fact.get('cpu_hyperthreading') is not None:
            fingerprint['cpu_hyperthreading'] = fact['cpu_hyperthreading']

        if fact.get('cpu_socket_count'):
            fingerprint['cpu_socket_count'] = fact['cpu_socket_count']

        if fact.get('cpu_core_count'):
            fingerprint['cpu_core_count'] = fact['cpu_core_count']

        # Determine system_creation_date
        system_creation_date = None
        if fact.get('date_anaconda_log'):
            system_creation_date = datetime.strptime(
                fact['date_anaconda_log'], '%Y-%m-%d')

        if system_creation_date and fact.get('date_yum_history'):
            date_yum_history = datetime.strptime(
                fact['date_yum_history'], '%Y-%m-%d')
            if date_yum_history < system_creation_date:
                system_creation_date = date_yum_history

        if system_creation_date:
            fingerprint['system_creation_date'] = system_creation_date.date()

        # Determine if running on VM or bare metal
        if fact.get('virt_what_type') or fact.get('virt_type'):
            if fact.get('virt_what_type') == 'bare metal':
                fingerprint['infrastructure_type'] = 'bare_metal'
            elif fact.get('virt_type'):
                fingerprint['infrastructure_type'] = 'virtualized'
            else:
                # virt_what_type is not bare metal or None
                # (since both cannot be)
                fingerprint['infrastructure_type'] = 'unknown'
        else:
            fingerprint['infrastructure_type'] = 'unknown'

        # Determine if VM facts
        fingerprint['virtualized_is_guest'] = bool(
            fact.get('virt_virt') == 'virt-guest')

        if fact.get('virt_type'):
            fingerprint['virtualized_type'] = fact['virt_type']

        if fact.get('virt_num_guests'):
            fingerprint['virtualized_num_guests'] = fact['virt_num_guests']

        if fact.get('virt_num_running_guests'):
            fingerprint['virtualized_num_running_guests'] =\
                fact['virt_num_running_guests']

        return fingerprint


FINGERPRINT_ENGINE = Engine()

# pylint: disable=C0103
pfc_signal = django.dispatch.Signal(providing_args=[
    'instance'])

pfc_signal.connect(process_fact_collection)
