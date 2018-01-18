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
import uuid
from datetime import datetime
import django.dispatch
from api.fact.util import read_raw_facts
from api.models import FactCollection, Source
from api.serializers import FingerprintSerializer

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

NETWORK_IDENTIFICATION_KEYS = ['subscription_manager_id',
                               'bios_uuid']
VCENTER_IDENTIFICATION_KEYS = ['vm_uuid']
COMMON_FACTS_TO_MERGE = ['os_name',
                         'os_version',
                         'os_release',
                         'mac_addresses',
                         'ip_addresses',
                         'cpu_count']
VCENTER_FACTS_TO_MERGE = ['vm_name',
                          'vm_state',
                          'vm_uuid',
                          'vm_memory_size',
                          'vm_dns_name',
                          'vm_host',
                          'vm_host_cpu_cores',
                          'vm_host_cpu_threads',
                          'vm_host_socket_count',
                          'vm_datacenter',
                          'vm_cluster']
FINGERPRINT_GLOBAL_ID_KEY = 'FINGERPRINT_GLOBAL_ID'


def process_fact_collection(sender, instance, **kwargs):
    """Process the fact collection.

    :param sender: Class that was saved
    :param instance: FactCollection that was saved
    :param facts: dict of raw facts
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument

    raw_facts = read_raw_facts(instance.id)

    # Invoke ENGINE to create fingerprints from facts
    fingerprints_list = _process_sources(raw_facts)

    number_valid = 0
    number_invalid = 0
    for fingerprint_dict in fingerprints_list:
        serializer = FingerprintSerializer(data=fingerprint_dict)
        if serializer.is_valid():
            number_valid += 1
            serializer.save()
        else:
            number_invalid += 1
            logger.error('Fingerprint engine could not persist fingerprint.')
            logger.error('Invalid fingerprint: %s', fingerprint_dict)
            logger.error('Fingerprint errors: %s', serializer.errors)

    logger.debug('FactCollection %d produced %d valid '
                 'fingerprints and %d invalid fingerprints.',
                 instance.id,
                 number_valid,
                 number_invalid)

    # Mark completed because engine has process raw facts
    instance.status = FactCollection.FC_STATUS_COMPLETE
    instance.save()


def _process_sources(raw_facts):
    """Process facts and convert to fingerprints.

    :param raw_facts: Collected raw facts for all sources
    :returns: list of fingerprints for all systems (all scans)
    """
    network_fingerprints = []
    vcenter_fingerprints = []
    for source in raw_facts['sources']:
        source_fingerprints = _process_source(
            raw_facts['fact_collection_id'],
            source)
        if source['source_type'] == Source.NETWORK_SOURCE_TYPE:
            network_fingerprints += source_fingerprints
        elif source['source_type'] == Source.VCENTER_SOURCE_TYPE:
            vcenter_fingerprints += source_fingerprints

    # Deduplicate network fingerprints
    number_before = len(network_fingerprints)
    network_fingerprints = _remove_duplicate_fingerprints(
        NETWORK_IDENTIFICATION_KEYS,
        network_fingerprints)

    number_after = len(network_fingerprints)
    logger.debug('Remove duplicate network fingerprints.')
    logger.debug('Number before: %d, Number after: %d',
                 number_before, number_after)

    # Deduplicate vcenter fingerprints
    number_before = len(vcenter_fingerprints)
    vcenter_fingerprints = _remove_duplicate_fingerprints(
        VCENTER_IDENTIFICATION_KEYS,
        vcenter_fingerprints)

    number_after = len(vcenter_fingerprints)
    logger.debug('Remove duplicate vcenter fingerprints.')
    logger.debug('Number before: %d, Number after: %d',
                 number_before, number_after)

    # Merge network and vcenter fingerprints
    logger.debug('Merging network and vcenter fingerprints.')
    number_before = len(network_fingerprints) + len(vcenter_fingerprints)
    all_fingerprints = _merge_network_and_vcenter(
        network_fingerprints, vcenter_fingerprints)
    number_after = len(all_fingerprints)
    logger.debug('Merged network and vcenter fingerprints.')
    logger.debug('Number before: %d, Number after: %d',
                 number_before, number_after)

    return all_fingerprints


def _process_source(fact_collection_id, source):
    """Process facts and convert to fingerprints.

    :param fact_collection_id: id of fact collection
    associated with facts
    :param source_id: id of source associated with facts
    :param source_type: the type of source (network, vcenter, etc)
    :param facts: facts to process
    :returns: fingerprints produced from facts
    """
    fingerprints = []
    for fact in source['facts']:
        fingerprint = None
        if source['source_type'] == Source.NETWORK_SOURCE_TYPE:
            fingerprint = _process_network_fact(fact)
        else:
            fingerprint = _process_vcenter_fact(fact)
        fingerprint['fact_collection_id'] = fact_collection_id
        fingerprint['source_id'] = source['source_id']
        fingerprint['source_type'] = source['source_type']
        fingerprints.append(fingerprint)
    return fingerprints


def _merge_network_and_vcenter(network_fingerprints,
                               vcenter_fingerprints):
    """Merge facts from multiple sources.

    :param network_fingerprints: fact to process
    :param vcenter_fingerprints: fact to process
    :returns: list of all fingerprints wihtout duplicates
    """
    # Check to make sure a merge is required at all
    if not vcenter_fingerprints:
        return network_fingerprints

    if not network_fingerprints:
        return vcenter_fingerprints

    # start with the network fingerprints as base set
    result = network_fingerprints[:]
    to_merge = vcenter_fingerprints[:]

    result, to_merge = _merge_matching_fingerprints(
        'bios_uuid', result, 'vm_uuid', to_merge)

    result, to_merge = _merge_matching_fingerprints(
        'mac_addresses', result, 'mac_addresses', to_merge)

    # Add remaining as they didn't match anything (no merge)
    result = result + to_merge
    return result


def _merge_matching_fingerprints(base_key, base_list,
                                 candidate_key, candidate_list):
    """Given keys and two lists, merge on key equality.

    Given two lists of fingerprints, match on provided keys and merge
    if keys match.  Base values have precedence.
    :param base_key: base_key used to create an index of base_list
    :param base_list: list of dict objects
    :param candidate_key: candidate_key used to create an index of
    candidate_list
    :param candidate_list: list of dict objects
    :returns: fingerprint produced from fact
    """
    # pylint: disable=too-many-locals,consider-iterating-dictionary
    base_dict, base_no_key = _create_index_for_fingerprint(
        base_key, base_list)
    candidate_dict, candidate_no_key = _create_index_for_fingerprint(
        candidate_key, candidate_list)

    # Initialize lists with values that cannot be compared
    base_match_list = []
    candidate_no_match_list = []

    # Match candidate to base fingerprint using index key
    for candidate_index_key, candidate_fingerprint in candidate_dict.items():
        # For each overlay fingerprint check for matching base fingerprint
        # using candidate_index_key.  Remove so value is not in
        # left-over set
        base_value = base_dict.pop(candidate_index_key, None)
        if base_value:
            # candidate_index_key == base_key so merge
            logger.debug('Fingerprints matched on %s/%s with value %s',
                         base_key, candidate_key, candidate_index_key)
            merged_value = _merge_fingerprint(
                base_value, candidate_fingerprint)

            # Add merged value to key
            base_match_list.append(merged_value)
        else:
            # Could not merge, so add to not merged list
            candidate_no_match_list.append(candidate_fingerprint)

    # Merge base items without key, matched, and remainder
    # who did not match
    base_result_list = _remove_duplicate_fingerprints(
        [FINGERPRINT_GLOBAL_ID_KEY],
        base_no_key + base_match_list +
        list(base_dict.values()),
        True)

    # Merge candidate items without key list with those that didn't match
    candidate_no_match_list = _remove_duplicate_fingerprints(
        [FINGERPRINT_GLOBAL_ID_KEY],
        candidate_no_key +
        candidate_no_match_list,
        True)

    return base_result_list, candidate_no_match_list


def _remove_duplicate_fingerprints(id_key_list,
                                   fingerprint_list,
                                   remove_key=False):
    """Given a list of dict remove duplicates.

    Takes fingerprint_list and retrieves dict value for
    FINGERPRINT_GLOBAL_ID_KEY. Builds a map using this.  A
    fingerprint that was duplicated for mac_address comparision will
    have the samme FINGERPRINT_GLOBAL_ID_KEY.
    :param id_key_list: keys used to evaulate uniqueness
    :param fingerprint_list: list of dict objects to be keyed by id_key
    :param remove_key: bool that determines if the id_key and its value
    should be removed from fingerprint
    :returns: list of fingerprints that is unique
    """
    result_list = fingerprint_list[:]
    for id_key in id_key_list:
        unique_dict = {}
        no_global_id_list = []
        for fingerprint in result_list:
            unique_id_value = fingerprint.get(id_key)
            if unique_id_value:
                # Add or update fingerprint value
                unique_dict[unique_id_value] = fingerprint
            else:
                no_global_id_list.append(fingerprint)

        result_list = no_global_id_list + list(unique_dict.values())

        # Strip id key from fingerprints if requested
        if remove_key:
            for fingerprint in result_list:
                unique_id_value = fingerprint.get(id_key)
                if unique_id_value:
                    del fingerprint[id_key]

    return result_list


def _create_index_for_fingerprint(id_key,
                                  fingerprint_list,
                                  create_global_id=True):
    """Given a list of dict, create index by id_key.

    Takes fingerprint_list and retrieves dict value for id_key.
    Adds this to a result dict by id_key values.  For example,
    given a list of system fact dict, creates a dict of systems
    by mac_address.
    :param id_key: key to use in dict creation
    :param fingerprint_list: list of dict objects to be keyed by id_key
    :param create_global_id: If True, a new key/value is placed in the
    index.  The key is FINGERPRINT_GLOBAL_ID_KEY and the value is a newly
    generated UUID.  This allows you to de-duplicate later if needed.
    :returns: dict of values keyed by id_key and list of values
    who do not have the id_key
    """
    result_by_key = {}
    key_not_found_list = []
    for value_dict in fingerprint_list:
        # Add globally unique key for de-duplication later
        if create_global_id:
            value_dict[FINGERPRINT_GLOBAL_ID_KEY] = str(uuid.uuid4())
        id_key_value = value_dict.get(id_key)
        if id_key_value:
            if isinstance(id_key_value, list):
                # value is list so explode
                for list_value in id_key_value:
                    result_by_key[list_value] = value_dict
            else:
                result_by_key[id_key_value] = value_dict
        else:
            key_not_found_list.append(value_dict)
    return result_by_key, key_not_found_list


def _merge_fingerprint(network_fingerprint, vcenter_fingerprint):
    """Merge network and vcenter facts."""
    # Add vcenter fact if not already set by network

    logger.debug('Merging the following two fingerprints.')
    logger.debug('Network fingerprint: %s', network_fingerprint)
    logger.debug('VCenter fingerprint: %s', vcenter_fingerprint)

    for fact in COMMON_FACTS_TO_MERGE:
        existing_nfact = network_fingerprint.get(fact)
        new_vfact = vcenter_fingerprint.get(fact)
        if not existing_nfact and new_vfact:
            network_fingerprint[fact] = new_vfact

    # Add vcenter facts
    for fact in VCENTER_FACTS_TO_MERGE:
        new_vfact = vcenter_fingerprint.get(fact)
        if new_vfact:
            network_fingerprint[fact] = new_vfact

    logger.debug('Merged fingerprint: %s', network_fingerprint)

    return network_fingerprint


def _process_network_fact(fact):
    """Process a fact and convert to a fingerprint.

    :param facts: fact to process
    :returns: fingerprint produced from fact
    """
    # pylint: disable=too-many-branches,too-many-statements

    fingerprint = {}
    # Common facts
    if fact.get('connection_host'):
        fingerprint['name'] = fact['connection_host']

    # Set OS information
    if fact.get('etc_release_name'):
        fingerprint['os_name'] = fact.get('etc_release_name')

    if fact.get('etc_release_version'):
        fingerprint['os_version'] = fact['etc_release_version']

    if fact.get('etc_release_release'):
        fingerprint['os_release'] = fact['etc_release_release']

    # Set ip address from either network or vcenter
    if fact.get('ifconfig_ip_addresses'):
        fingerprint['ip_addresses'] = fact['ifconfig_ip_addresses']

    # Set mac address from either network or vcenter
    if fact.get('ifconfig_mac_addresses'):
        fingerprint['mac_addresses'] = fact['ifconfig_mac_addresses']

    # Set CPU facts
    if fact.get('cpu_count'):
        fingerprint['cpu_count'] = fact['cpu_count']

    # Network scan specific facts
    # Set bios UUID
    if fact.get('dmi_system_uuid'):
        fingerprint['bios_uuid'] = fact['dmi_system_uuid']

    # Set subscription manager id
    if fact.get('subman_virt_uuid'):
        fingerprint['subscription_manager_id'] = fact['subman_virt_uuid']

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


def _process_vcenter_fact(fact):
    """Process a fact and convert to a fingerprint.

    :param facts: fact to process
    :returns: fingerprint produced from fact
    """
    # pylint: disable=too-many-branches

    fingerprint = {}

    # Common facts
    # Set name
    if fact.get('vm.name'):
        fingerprint['name'] = fact['vm.name']

    # Set vm.os
    if fact.get('vm.os'):
        fingerprint['os_release'] = fact['vm.os']

    fingerprint['infrastructure_type'] = 'virtualized'
    fingerprint['virtualized_is_guest'] = True

    # Set mac address from either network or vcenter
    if fact.get('vm.mac_addresses'):
        fingerprint['mac_addresses'] = fact['vm.mac_addresses']

    # Set vm.ip_address
    if fact.get('vm.ip_addresses'):
        fingerprint['ip_addresses'] = fact['vm.ip_addresses']

    # Set vm.cpu_count
    if fact.get('vm.cpu_count'):
        fingerprint['cpu_count'] = fact['vm.cpu_count']

    # VCenter specific facts
    # Set vm.state
    if fact.get('vm.state'):
        fingerprint['vm_state'] = fact['vm.state']

    # Set vm.uuid
    if fact.get('vm.uuid'):
        fingerprint['vm_uuid'] = fact['vm.uuid']

    # Set vm.memory_size
    if fact.get('vm.memory_size'):
        fingerprint['vm_memory_size'] = fact['vm.memory_size']

    # Set vm.dns_name
    if fact.get('vm.dns_name'):
        fingerprint['vm_dns_name'] = fact['vm.dns_name']

    # Set vm.host.name
    if fact.get('vm.host.name'):
        fingerprint['vm_host'] = fact['vm.host.name']

    # Set vm.host.cpu_cores
    if fact.get('vm.host.cpu_cores'):
        fingerprint['vm_host_cpu_cores'] = fact['vm.host.cpu_cores']

    # Set vm.host.cpu_threads
    if fact.get('vm.host.cpu_threads'):
        fingerprint['vm_host_cpu_threads'] = fact['vm.host.cpu_threads']

    # Set vm.host.cpu_count
    if fact.get('vm.host.cpu_count'):
        fingerprint['vm_host_socket_count'] = fact['vm.host.cpu_count']

    # Set vm.datacenter
    if fact.get('vm.datacenter'):
        fingerprint['vm_datacenter'] = fact['vm.datacenter']

    # Set vm.cluster
    if fact.get('vm.cluster'):
        fingerprint['vm_cluster'] = fact['vm.cluster']

    return fingerprint


# pylint: disable=C0103
pfc_signal = django.dispatch.Signal(providing_args=[
    'instance'])

pfc_signal.connect(process_fact_collection)
