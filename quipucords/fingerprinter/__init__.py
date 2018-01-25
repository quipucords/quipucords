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
from api.models import FactCollection, Source
from api.serializers import FingerprintSerializer

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Keys used to de-duplicate against other network sources
NETWORK_IDENTIFICATION_KEYS = ['subscription_manager_id',
                               'bios_uuid']

# Keys used to de-duplicate against other VCenter sources
VCENTER_IDENTIFICATION_KEYS = ['vm_uuid']

# Keys used to de-duplicate against other satellite sources
SATELLITE_IDENTIFICATION_KEYS = ['subscription_manager_id']

# Keys used to de-duplicate against across sources
NETWORK_SATELLITE_MERGE_KEYS = [
    ('subscription_manager_id', 'subscription_manager_id'),
    ('mac_addresses', 'mac_addresses')]
NETWORK_VCENTER_MERGE_KEYS = [
    ('bios_uuid', 'vm_uuid'),
    ('mac_addresses', 'mac_addresses')]

FINGERPRINT_GLOBAL_ID_KEY = 'FINGERPRINT_GLOBAL_ID'

META_DATA_KEY = 'metadata'


def process_fact_collection(sender, instance, **kwargs):
    """Process the fact collection.

    :param sender: Class that was saved
    :param instance: FactCollection that was saved
    :param facts: dict of raw facts
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument

    # Invoke ENGINE to create fingerprints from facts
    fingerprints_list = _process_sources(instance)

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


def _process_sources(fact_collection):
    """Process facts and convert to fingerprints.

    :param json_fact_collection: Collected raw facts for all sources
    :returns: list of fingerprints for all systems (all scans)
    """
    network_fingerprints = []
    vcenter_fingerprints = []
    satellite_fingerprints = []
    for source in fact_collection.get_sources():
        source_fingerprints = _process_source(fact_collection.id,
                                              source)
        if source['source_type'] == Source.NETWORK_SOURCE_TYPE:
            network_fingerprints += source_fingerprints
        elif source['source_type'] == Source.VCENTER_SOURCE_TYPE:
            vcenter_fingerprints += source_fingerprints
        elif source['source_type'] == Source.SATELLITE_SOURCE_TYPE:
            satellite_fingerprints += source_fingerprints

    # Deduplicate network fingerprints
    number_before = len(network_fingerprints)
    network_fingerprints = _remove_duplicate_fingerprints(
        NETWORK_IDENTIFICATION_KEYS,
        network_fingerprints)

    number_after = len(network_fingerprints)
    logger.debug('Remove duplicate network fingerprints.')
    logger.debug('Number before: %d, Number after: %d',
                 number_before, number_after)

    # Deduplicate satellite fingerprints
    number_before = len(satellite_fingerprints)
    satellite_fingerprints = _remove_duplicate_fingerprints(
        SATELLITE_IDENTIFICATION_KEYS,
        satellite_fingerprints)

    number_after = len(satellite_fingerprints)
    logger.debug('Remove duplicate satellite fingerprints.')
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

    # Merge network and satellite fingerprints
    logger.debug('Merging network and satellite fingerprints.')
    number_before = len(network_fingerprints) + len(satellite_fingerprints)
    all_fingerprints = _merge_fingerprints_from_source_types(
        NETWORK_SATELLITE_MERGE_KEYS,
        network_fingerprints,
        satellite_fingerprints)
    number_after = len(all_fingerprints)
    logger.debug('Merged network and satellite fingerprints.')
    logger.debug('Number before: %d, Number after: %d',
                 number_before, number_after)

    # Merge network and vcenter fingerprints
    logger.debug('Merging network and vcenter fingerprints.')
    number_before = len(all_fingerprints) + len(vcenter_fingerprints)
    all_fingerprints = _merge_fingerprints_from_source_types(
        NETWORK_VCENTER_MERGE_KEYS,
        all_fingerprints,
        vcenter_fingerprints)
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
        source_type = source['source_type']
        if source_type == Source.NETWORK_SOURCE_TYPE:
            fingerprint = _process_network_fact(source, fact)
        elif source_type == Source.VCENTER_SOURCE_TYPE:
            fingerprint = _process_vcenter_fact(source, fact)
        elif source_type == Source.SATELLITE_SOURCE_TYPE:
            fingerprint = _process_satellite_fact(source, fact)
        else:
            logger.error('Could not process source, unknown source type: %s',
                         source_type)

        if fingerprint is not None:
            fingerprint['fact_collection_id'] = fact_collection_id
            fingerprints.append(fingerprint)

    return fingerprints


def _merge_fingerprints_from_source_types(merge_keys_list, base_list,
                                          merge_list):
    """Merge fingerprints from multiple sources.

    :param base_list: base list
    :param merge_list: fact to process
    :returns: list of all fingerprints wihtout duplicates
    """
    # Check to make sure a merge is required at all
    if not merge_list:
        return base_list

    if not base_list:
        return merge_list

    # start with the base_list fingerprints
    result = base_list[:]
    to_merge = merge_list[:]
    for key_tuple in merge_keys_list:
        result, to_merge = _merge_matching_fingerprints(
            key_tuple[0], result, key_tuple[1], to_merge)

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
    if not fingerprint_list:
        return fingerprint_list

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


def _merge_fingerprint(priority_fingerprint, to_merge_fingerprint):
    """Merge two fingerprints.

    The priority_fingerprint values are always used.  The
    to_merge_fingerprint values are only used when the priority_fingerprint
    is missing the same values.
    :param priority_fingerprint: Fingerprint that has precedence if
    both have the same attribute.
    :param to_merge_fingerprint: Fingerprint whose values are used
    when attributes are not in priority_fingerprint
    """
    priority_keys = set(priority_fingerprint.keys())
    to_merge_keys = set(to_merge_fingerprint.keys())

    keys_to_add_list = list(to_merge_keys - priority_keys)
    if META_DATA_KEY in keys_to_add_list:
        keys_to_add_list.remove(META_DATA_KEY)

    logger.debug('Merging the following two fingerprints.')
    logger.debug('Base fingerprint: %s', priority_fingerprint)
    logger.debug('Overlay fingerprint: %s', to_merge_fingerprint)

    # Add vcenter facts
    for fact_key in keys_to_add_list:
        to_merge_fact = to_merge_fingerprint.get(fact_key)
        if to_merge_fact:
            priority_fingerprint[META_DATA_KEY][fact_key] = \
                to_merge_fingerprint[META_DATA_KEY][fact_key]
            priority_fingerprint[fact_key] = to_merge_fact

    logger.debug('Merged fingerprint: %s', priority_fingerprint)

    return priority_fingerprint


def add_fact_to_fingerprint(source,
                            raw_fact_key,
                            raw_fact,
                            fingerprint_key,
                            fingerprint,
                            fact_value=None):
    """Create the fingerprint fact and metadata.

    :param source: Source used to gather raw facts.
    :param raw_fact_key: Raw fact key used to obtain value
    :param raw_fact: Raw fact used used to obtain value
    :param fingerprint_key: Key used to store fingerprint
    :param fingerprint: dict containing all fingerprint facts
    this fact.
    :param fact_value: Used when values are computed from
    raw facts instead of direct access.
    """
    # pylint: disable=too-many-arguments
    actual_fact_value = None
    if fact_value is not None:
        actual_fact_value = fact_value
    elif raw_fact.get(raw_fact_key) is not None:
        actual_fact_value = raw_fact.get(raw_fact_key)

    if actual_fact_value is not None:
        fingerprint[fingerprint_key] = actual_fact_value
        fingerprint[META_DATA_KEY][fingerprint_key] = {
            'source_id': source['source_id'],
            'source_type': source['source_type'],
            'raw_fact_key': raw_fact_key
        }


def _process_network_fact(source, fact):
    """Process a fact and convert to a fingerprint.

    :param source: The source that provided this fact.
    :param facts: fact to process
    :returns: fingerprint produced from fact
    """
    fingerprint = {META_DATA_KEY: {}}

    # Common facts
    add_fact_to_fingerprint(source, 'connection_host',
                            fact, 'name', fingerprint)

    # Set OS information
    add_fact_to_fingerprint(source, 'etc_release_name',
                            fact, 'os_name', fingerprint)
    add_fact_to_fingerprint(source, 'etc_release_version',
                            fact, 'os_version', fingerprint)
    add_fact_to_fingerprint(source, 'etc_release_release',
                            fact, 'os_release', fingerprint)

    # Set ip address from either network or vcenter
    add_fact_to_fingerprint(source, 'ifconfig_ip_addresses',
                            fact, 'ip_addresses', fingerprint)

    # Set mac address from either network or vcenter
    add_fact_to_fingerprint(source, 'ifconfig_mac_addresses',
                            fact, 'mac_addresses', fingerprint)

    # Set CPU facts
    add_fact_to_fingerprint(source, 'cpu_count',
                            fact, 'cpu_count', fingerprint)

    # Network scan specific facts
    # Set bios UUID
    add_fact_to_fingerprint(source, 'dmi_system_uuid',
                            fact, 'bios_uuid', fingerprint)

    # Set subscription manager id
    add_fact_to_fingerprint(source, 'subman_virt_uuid',
                            fact, 'subscription_manager_id', fingerprint)

    # System information
    add_fact_to_fingerprint(source, 'cpu_core_per_socket',
                            fact, 'cpu_core_per_socket', fingerprint)
    add_fact_to_fingerprint(source, 'cpu_siblings',
                            fact, 'cpu_siblings', fingerprint)
    add_fact_to_fingerprint(source, 'cpu_hyperthreading',
                            fact, 'cpu_hyperthreading', fingerprint)
    add_fact_to_fingerprint(source, 'cpu_socket_count',
                            fact, 'cpu_socket_count', fingerprint)
    add_fact_to_fingerprint(source, 'cpu_core_count',
                            fact, 'cpu_core_count', fingerprint)

    # Determine system_creation_date
    system_creation_date = None
    raw_fact_key = None
    if fact.get('date_anaconda_log'):
        raw_fact_key = 'date_anaconda_log'
        system_creation_date = datetime.strptime(
            fact['date_anaconda_log'], '%Y-%m-%d')

    if system_creation_date and fact.get('date_yum_history'):
        date_yum_history = datetime.strptime(
            fact['date_yum_history'], '%Y-%m-%d')
        if date_yum_history < system_creation_date:
            raw_fact_key = 'date_yum_history'
            system_creation_date = date_yum_history

    if system_creation_date:
        add_fact_to_fingerprint(source, raw_fact_key, fact,
                                'system_creation_date',
                                fingerprint,
                                fact_value=system_creation_date.date())

    # Determine if running on VM or bare metal
    virt_what_type = fact.get('virt_what_type')
    virt_type = fact.get('virt_type')
    if virt_what_type or virt_type:
        if virt_what_type == 'bare metal':
            add_fact_to_fingerprint(
                source, 'virt_what_type', fact, 'infrastructure_type',
                fingerprint, fact_value='bare_metal')
        elif virt_type:
            add_fact_to_fingerprint(
                source, 'virt_type', fact, 'infrastructure_type',
                fingerprint, fact_value='virtualized')
        else:
            # virt_what_type is not bare metal or None
            # (since both cannot be)
            add_fact_to_fingerprint(
                source, 'virt_what_type', fact, 'infrastructure_type',
                fingerprint, fact_value='unknown')
    else:
        add_fact_to_fingerprint(
            source, 'virt_what_type/virt_type', fact, 'infrastructure_type',
            fingerprint, fact_value='unknown')

    # Determine if VM facts
    add_fact_to_fingerprint(
        source, 'virt_virt/virt-guest', fact, 'virtualized_is_guest',
        fingerprint, fact_value=bool(
            fact.get('virt_virt') == 'virt-guest'))

    add_fact_to_fingerprint(source, 'virt_type', fact,
                            'virtualized_type', fingerprint)
    add_fact_to_fingerprint(source, 'virt_num_guests',
                            fact, 'virtualized_num_guests', fingerprint)
    add_fact_to_fingerprint(source, 'virt_num_running_guests',
                            fact, 'virtualized_num_running_guests',
                            fingerprint)

    return fingerprint


def _process_vcenter_fact(source, fact):
    """Process a fact and convert to a fingerprint.

    :param source: The source that provided this fact.
    :param facts: fact to process
    :returns: fingerprint produced from fact
    """
    # pylint: disable=too-many-branches

    fingerprint = {META_DATA_KEY: {}}

    # Common facts
    # Set name
    add_fact_to_fingerprint(source, 'vm.name', fact, 'name', fingerprint)

    add_fact_to_fingerprint(source, 'vm.os', fact, 'os_release', fingerprint)

    add_fact_to_fingerprint(source, 'vcenter_source', fact,
                            'infrastructure_type', fingerprint,
                            fact_value='virtualized')
    add_fact_to_fingerprint(source, 'vcenter_source', fact,
                            'virtualized_is_guest', fingerprint,
                            fact_value=True)

    add_fact_to_fingerprint(source, 'vm.mac_addresses',
                            fact, 'mac_addresses', fingerprint)
    add_fact_to_fingerprint(source, 'vm.ip_addresses',
                            fact, 'ip_addresses', fingerprint)
    add_fact_to_fingerprint(source, 'vm.cpu_count',
                            fact, 'cpu_count', fingerprint)

    # VCenter specific facts
    add_fact_to_fingerprint(source, 'vm.state', fact, 'vm_state', fingerprint)
    add_fact_to_fingerprint(source, 'vm.uuid', fact, 'vm_uuid', fingerprint)
    add_fact_to_fingerprint(source, 'vm.memory_size',
                            fact, 'vm_memory_size', fingerprint)
    add_fact_to_fingerprint(source, 'vm.dns_name', fact,
                            'vm_dns_name', fingerprint)
    add_fact_to_fingerprint(source, 'vm.host.name',
                            fact, 'vm_host', fingerprint)
    add_fact_to_fingerprint(source, 'vm.host.cpu_cores',
                            fact, 'vm_host_cpu_cores', fingerprint)
    add_fact_to_fingerprint(source, 'vm.host.cpu_threads',
                            fact, 'vm_host_cpu_threads', fingerprint)
    add_fact_to_fingerprint(source, 'vm.host.cpu_count',
                            fact, 'vm_host_socket_count', fingerprint)
    add_fact_to_fingerprint(source, 'vm.datacenter',
                            fact, 'vm_datacenter', fingerprint)
    add_fact_to_fingerprint(source, 'vm.cluster', fact,
                            'vm_cluster', fingerprint)

    return fingerprint


def _process_satellite_fact(source, fact):
    """Process a fact and convert to a fingerprint.

    :param source: The source that provided this fact.
    :param facts: fact to process
    :returns: fingerprint produced from fact
    """
    # pylint: disable=too-many-branches

    fingerprint = {META_DATA_KEY: {}}

    # Common facts
    add_fact_to_fingerprint(source, 'hostname', fact, 'name', fingerprint)

    add_fact_to_fingerprint(source, 'os_release', fact,
                            'os_release', fingerprint)
    add_fact_to_fingerprint(source, 'os_name', fact, 'os_name', fingerprint)
    add_fact_to_fingerprint(source, 'os_version', fact,
                            'os_version', fingerprint)

    add_fact_to_fingerprint(source, 'mac_addresses',
                            fact, 'mac_addresses', fingerprint)
    add_fact_to_fingerprint(source, 'ip_addresses', fact,
                            'ip_addresses', fingerprint)

    add_fact_to_fingerprint(source, 'cores', fact, 'cpu_count', fingerprint)

    # Common network/satellite
    add_fact_to_fingerprint(source, 'uuid', fact,
                            'subscription_manager_id', fingerprint)
    add_fact_to_fingerprint(source, 'virt_type', fact,
                            'virtualized_type', fingerprint)

    is_virtualized = fact.get('is_virtualized')
    if is_virtualized:
        infrastructure_type = 'virtualized'
    else:
        infrastructure_type = 'unknown'
    add_fact_to_fingerprint(source, 'is_virtualized', fact,
                            'infrastructure_type', fingerprint,
                            fact_value=infrastructure_type)

    virtualized_is_guest = bool(
        fact.get('virt_type') and
        fact.get('virtual_host') != fact.get('hostname'))
    add_fact_to_fingerprint(source, 'virt_type/virtual_host/hostname', fact,
                            'virtualized_is_guest', fingerprint,
                            fact_value=virtualized_is_guest)

    # Satellite specific facts
    add_fact_to_fingerprint(source, 'cores', fact,
                            'cpu_core_count', fingerprint)
    add_fact_to_fingerprint(source, 'num_sockets', fact,
                            'cpu_socket_count', fingerprint)

    return fingerprint


# pylint: disable=C0103
pfc_signal = django.dispatch.Signal(providing_args=[
    'instance'])

pfc_signal.connect(process_fact_collection)
