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

"""Test the fact engine API."""

from datetime import datetime
from django.test import TestCase
from fingerprinter import (FINGERPRINT_GLOBAL_ID_KEY,
                           _process_source,
                           _remove_duplicate_fingerprints,
                           _merge_fingerprint,
                           _create_index_for_fingerprint,
                           _merge_matching_fingerprints,
                           _merge_network_and_vcenter)
from api.models import Source


class EngineTest(TestCase):
    """Tests Engine class."""

    # pylint: disable=no-self-use,too-many-arguments
    # pylint: disable=too-many-locals,too-many-branches,invalid-name
    # pylint: disable=protected-access

    ################################################################
    # Helper functions
    ################################################################
    def _create_network_fc_json(
            self,
            fact_collection_id=1,
            source_id=1,
            source_type=Source.NETWORK_SOURCE_TYPE,
            cpu_count=2,
            etc_release_name='RHEL',
            etc_release_version='7.4 (Maipo)',
            etc_release_release='RHEL 7.4 (Maipo)',
            ifconfig_ip_addresses=None,
            ifconfig_mac_addresses=None,
            dmi_system_uuid='1234',
            subman_virt_uuid='4567',
            connection_uuid='a037f26f-2988-57bd-85d8-de7617a3aab0',
            connection_host='1.2.3.4',
            connection_port=22,
            cpu_core_per_socket=1,
            cpu_siblings=1,
            cpu_hyperthreading=False,
            cpu_socket_count=2,
            cpu_core_count=2,
            date_anaconda_log='2017-06-17',
            date_yum_history='2017-07-18',
            virt_virt='virt-guest',
            virt_type='vmware',
            virt_num_guests=1,
            virt_num_running_guests=1,
            virt_what_type='vt'):
        """Create an in memory FactCollection for tests."""
        # pylint: disable=too-many-statements
        fact = {}
        if source_id:
            fact['source_id'] = source_id
        if source_type:
            fact['source_type'] = source_type
        if cpu_count:
            fact['cpu_count'] = cpu_count
        if etc_release_name:
            fact['etc_release_name'] = etc_release_name
        if etc_release_version:
            fact['etc_release_version'] = etc_release_version
        if etc_release_release:
            fact['etc_release_release'] = etc_release_release

        if ifconfig_ip_addresses:
            fact['ifconfig_ip_addresses'] = ifconfig_ip_addresses
        else:
            fact['ifconfig_ip_addresses'] = ['1.2.3.4', '2.3.4.5']

        if ifconfig_mac_addresses:
            fact['ifconfig_mac_addresses'] = ifconfig_mac_addresses
        else:
            fact['ifconfig_mac_addresses'] = ['MAC1', 'MAC2']

        if dmi_system_uuid:
            fact['dmi_system_uuid'] = dmi_system_uuid
        if subman_virt_uuid:
            fact['subman_virt_uuid'] = subman_virt_uuid
        if connection_uuid:
            fact['connection_uuid'] = connection_uuid
        if connection_host:
            fact['connection_host'] = connection_host
        if connection_port:
            fact['connection_port'] = connection_port
        if cpu_core_per_socket:
            fact['cpu_core_per_socket'] = cpu_core_per_socket
        if cpu_siblings:
            fact['cpu_siblings'] = cpu_siblings
        if cpu_hyperthreading is not None:
            fact['cpu_hyperthreading'] = cpu_hyperthreading
        if cpu_socket_count:
            fact['cpu_socket_count'] = cpu_socket_count
        if cpu_core_count:
            fact['cpu_core_count'] = cpu_core_count
        if date_anaconda_log:
            fact['date_anaconda_log'] = date_anaconda_log
        if date_yum_history:
            fact['date_yum_history'] = date_yum_history
        if virt_virt:
            fact['virt_virt'] = virt_virt
        if virt_type:
            fact['virt_type'] = virt_type
        if virt_num_guests:
            fact['virt_num_guests'] = virt_num_guests
        if virt_num_running_guests:
            fact['virt_num_running_guests'] = virt_num_running_guests
        if virt_what_type:
            fact['virt_what_type'] = virt_what_type

        fact_collection = {'id': fact_collection_id, 'facts': [fact]}
        return fact_collection

    def _create_vcenter_fc_json(
            self,
            fact_collection_id=1,
            source_id=1,
            source_type=Source.VCENTER_SOURCE_TYPE,
            vm_cpu_count=2,
            vm_os='RHEL 7.3',
            vm_mac_addresses=None,
            vm_ip_address=None,
            vm_name='TestMachine',
            vm_state='On',
            vm_uuid='a037f26f-2988-57bd-85d8-de7617a3aab0',
            vm_memory_size=1024,
            vm_dns_name='site.com',
            vm_host_name='1.2.3.4',
            vm_host_cpu_cores=2,
            vm_host_cpu_threads=4,
            vm_host_cpu_count=8,
            vm_datacenter='NY',
            vm_cluster='23sd'):
        """Create an in memory FactCollection for tests."""
        fact = {}
        if source_id:
            fact['source_id'] = source_id
        if source_type:
            fact['source_type'] = source_type
        if vm_cpu_count:
            fact['vm.cpu_count'] = vm_cpu_count
        if vm_os:
            fact['vm.os'] = vm_os

        if vm_ip_address:
            fact['vm.ip_addresses'] = vm_ip_address
        else:
            fact['vm.ip_addresses'] = ['1.2.3.4', '2.3.4.5']

        if vm_mac_addresses:
            fact['vm.mac_addresses'] = vm_mac_addresses
        else:
            fact['vm.mac_addresses'] = ['MAC1', 'MAC2']

        if vm_name:
            fact['vm.name'] = vm_name
        if vm_state:
            fact['vm.state'] = vm_state
        if vm_uuid:
            fact['vm.uuid'] = vm_uuid
        if vm_memory_size:
            fact['vm.memory_size'] = vm_memory_size
        if vm_dns_name:
            fact['vm.dns_name'] = vm_dns_name
        if vm_host_name:
            fact['vm.host.name'] = vm_host_name
        if vm_host_cpu_cores:
            fact['vm.host.cpu_cores'] = vm_host_cpu_cores
        if vm_host_cpu_threads:
            fact['vm.host.cpu_threads'] = vm_host_cpu_threads
        if vm_host_cpu_count:
            fact['vm.host.cpu_count'] = vm_host_cpu_count
        if vm_datacenter:
            fact['vm.datacenter'] = vm_datacenter
        if vm_cluster:
            fact['vm.cluster'] = vm_cluster

        fact_collection = {'id': fact_collection_id, 'facts': [fact]}
        return fact_collection

    def _validate_network_result(self, fingerprint, fact):
        """Help to validate fields."""
        self.assertEqual(fact.get('connection_host'),
                         fingerprint.get('name'))

        self.assertEqual(fact.get('etc_release_name'),
                         fingerprint.get('os_name'))
        self.assertEqual(fact.get('etc_release_release'),
                         fingerprint.get('os_release'))
        self.assertEqual(fact.get('etc_release_version'),
                         fingerprint.get('os_version'))

        self.assertListEqual(fact.get('ifconfig_ip_addresses'),
                             fingerprint.get('ip_addresses'))
        self.assertListEqual(fact.get('ifconfig_mac_addresses'),
                             fingerprint.get('mac_addresses'))

        self.assertEqual(fact.get('cpu_count'), fingerprint.get('cpu_count'))

        self.assertEqual(fact.get('dmi_system_uuid'),
                         fingerprint.get('bios_uuid'))
        self.assertEqual(fact.get('subman_virt_uuid'),
                         fingerprint.get('subscription_manager_id'))

        self.assertEqual(fact.get('cpu_core_per_socket'),
                         fingerprint.get('cpu_core_per_socket'))
        self.assertEqual(fact.get('cpu_siblings'),
                         fingerprint.get('cpu_siblings'))
        self.assertEqual(fact.get('cpu_hyperthreading'),
                         fingerprint.get('cpu_hyperthreading'))
        self.assertEqual(fact.get('cpu_socket_count'),
                         fingerprint.get('cpu_socket_count'))
        self.assertEqual(fact.get('cpu_core_count'),
                         fingerprint.get('cpu_core_count'))

        fact_date = datetime.strptime(
            fact.get('date_anaconda_log'), '%Y-%m-%d')
        fact_date = fact_date.date()

        self.assertEqual(fact_date, fingerprint.get('system_creation_date'))
        self.assertEqual('virtualized', fingerprint.get('infrastructure_type'))
        self.assertTrue(fingerprint.get('virtualized_is_guest'))

        self.assertEqual(fact.get('virt_type'),
                         fingerprint.get('virtualized_type'))
        self.assertEqual(fact.get('virt_num_guests'),
                         fingerprint.get('virtualized_num_guests'))
        self.assertEqual(fact.get('virt_num_running_guests'),
                         fingerprint.get('virtualized_num_running_guests'))

    def _validate_vcenter_result(self, fingerprint, fact):
        """Help to validate fields."""
        self.assertEqual(fact.get('vm.name'), fingerprint.get('name'))

        self.assertEqual(fact.get('vm.os'), fingerprint.get('os_release'))

        self.assertEqual(fact.get('vm.ip_addresses'),
                         fingerprint.get('ip_addresses'))
        self.assertEqual(fact.get('vm.mac_addresses'),
                         fingerprint.get('mac_addresses'))
        self.assertEqual(fact.get('vm.cpu_count'),
                         fingerprint.get('cpu_count'))

        self.assertEqual(fact.get('vm.state'),
                         fingerprint.get('vm_state'))

        self.assertEqual(fact.get('vm.uuid'), fingerprint.get('vm_uuid'))
        self.assertEqual(fact.get('vm.memory_size'),
                         fingerprint.get('vm_memory_size'))

        self.assertEqual(fact.get('vm.dns_name'),
                         fingerprint.get('vm_dns_name'))
        self.assertEqual(fact.get('vm.host.name'),
                         fingerprint.get('vm_host'))
        self.assertEqual(fact.get('vm.host.cpu_cores'),
                         fingerprint.get('vm_host_cpu_cores'))
        self.assertEqual(fact.get('vm.host.cpu_threads'),
                         fingerprint.get('vm_host_cpu_threads'))

        self.assertEqual(fact.get('vm.host.cpu_count'),
                         fingerprint.get('vm_host_socket_count'))
        self.assertEqual(fact.get('vm.datacenter'),
                         fingerprint.get('vm_datacenter'))
        self.assertEqual(fact.get('vm.cluster'),
                         fingerprint.get('vm_cluster'))

    def _create_network_fingerprint(self, *args, **kwargs):
        """Create test network fingerprint."""
        n_fact_collection = self._create_network_fc_json(*args, **kwargs)
        nfact = n_fact_collection['facts'][0]
        source = {'source_id': 1,
                  'source_type': Source.NETWORK_SOURCE_TYPE,
                  'facts': n_fact_collection['facts']}
        nfingerprints = _process_source(n_fact_collection['id'],
                                        source)
        nfingerprint = nfingerprints[0]
        self._validate_network_result(nfingerprint, nfact)

        return nfingerprint

    def _create_vcenter_fingerprint(self, *args, **kwargs):
        """Create test network/vcenter fingerprints."""
        v_fact_collection = self._create_vcenter_fc_json(*args, **kwargs)
        vfact = v_fact_collection['facts'][0]
        source = {'source_id': 2,
                  'source_type': Source.VCENTER_SOURCE_TYPE,
                  'facts': v_fact_collection['facts']}
        vfingerprints = _process_source(v_fact_collection['id'],
                                        source)
        vfingerprint = vfingerprints[0]
        self._validate_vcenter_result(vfingerprint, vfact)
        return vfingerprint

    ################################################################
    # Test Source functions
    ################################################################
    def test_process_network_source(self):
        """Test process network source."""
        fact_collection = self._create_network_fc_json()
        fact = fact_collection['facts'][0]
        source = {'source_id': 1,
                  'source_type': Source.NETWORK_SOURCE_TYPE,
                  'facts': fact_collection['facts']}
        fingerprints = _process_source(fact_collection['id'],
                                       source)
        fingerprint = fingerprints[0]
        self._validate_network_result(fingerprint, fact)

    def test_process_vcenter_source(self):
        """Test process vcenter source."""
        fact_collection = self._create_vcenter_fc_json()
        fact = fact_collection['facts'][0]
        source = {'source_id': 1,
                  'source_type': Source.VCENTER_SOURCE_TYPE,
                  'facts': fact_collection['facts']}
        fingerprints = _process_source(fact_collection['id'],
                                       source)
        fingerprint = fingerprints[0]
        self._validate_vcenter_result(fingerprint, fact)

    ################################################################
    # Test merge functions
    ################################################################
    def test_merge_network_and_vcenter(self):
        """Test merge of two lists of fingerprints."""
        nfingerprints = [
            self._create_network_fingerprint(dmi_system_uuid='match',
                                             ifconfig_mac_addresses=['1']),
            self._create_network_fingerprint(dmi_system_uuid='1',
                                             ifconfig_mac_addresses=['2'])]
        vfingerprints = [
            self._create_vcenter_fingerprint(vm_uuid='match'),
            self._create_vcenter_fingerprint(vm_uuid='2')]

        result_fingerprints = _merge_network_and_vcenter(
            nfingerprints, vfingerprints)

        self.assertEqual(len(result_fingerprints), 3)

    def test_merge_matching_fingerprints(self):
        """Test merge of two lists of fingerprints."""
        nmetadata = {
            'os_release': {
                'source_id': 1,
                'source_type': Source.NETWORK_SOURCE_TYPE,
                'raw_fact_key': 'etc_release_release'
            },
            'bios_uuid': {
                'source_id': 1,
                'source_type': Source.NETWORK_SOURCE_TYPE,
                'raw_fact_key': 'dmi_system_uuid'
            }

        }
        nfingerprint_to_merge = {
            'id': 1, 'os_release': 'RHEL 7', 'bios_uuid': 'match',
            'metadata': nmetadata}
        nfingerprint_no_match = {
            'id': 2, 'os_release': 'RHEL 7', 'bios_uuid': '2345',
            'metadata': nmetadata}
        nfingerprint_no_key = {
            'id': 3, 'os_release': 'RHEL 6', 'metadata': nmetadata}
        nfingerprints = [
            nfingerprint_to_merge,
            nfingerprint_no_match,
            nfingerprint_no_key
        ]

        vmetadata = {
            'os_release': {
                'source_id': 1,
                'source_type': Source.NETWORK_SOURCE_TYPE,
                'raw_fact_key': 'etc_release_release'
            },
            'vm_uuid': {
                'source_id': 1,
                'source_type': Source.NETWORK_SOURCE_TYPE,
                'raw_fact_key': 'vm.uuid'
            }

        }
        vfingerprint_to_merge = {
            'id': 5, 'os_release': 'Windows 7', 'vm_uuid': 'match',
            'metadata': vmetadata}
        vfingerprint_no_match = {
            'id': 6, 'os_release': 'RHEL 7', 'vm_uuid': '9876',
            'metadata': vmetadata}
        vfingerprint_no_key = {
            'id': 7, 'os_release': 'RHEL 6', 'metadata': vmetadata}
        vfingerprints = [
            vfingerprint_to_merge,
            vfingerprint_no_match,
            vfingerprint_no_key
        ]

        merge_list, no_match_found_list = _merge_matching_fingerprints(
            'bios_uuid', nfingerprints, 'vm_uuid', vfingerprints)

        # merge list should always contain all nfingerprints (base_list)
        self.assertEqual(len(merge_list), 3)
        self.assertTrue(nfingerprint_to_merge in merge_list)
        self.assertTrue(nfingerprint_no_match in merge_list)
        self.assertTrue(nfingerprint_no_key in merge_list)

        # assert VM property merged
        self.assertIsNotNone(nfingerprint_to_merge.get('vm_uuid'))

        # assert network os_release had priority
        self.assertEqual(nfingerprint_to_merge.get('os_release'), 'RHEL 7')

        # assert those that didn't match, don't have VM properties
        self.assertIsNone(nfingerprint_no_match.get('vm_uuid'))
        self.assertIsNone(nfingerprint_no_key.get('vm_uuid'))

        # no_match_found list should only contain vfingerprints
        #  with no match
        self.assertEqual(len(no_match_found_list), 2)
        self.assertTrue(vfingerprint_no_match in no_match_found_list)
        self.assertTrue(vfingerprint_no_key in no_match_found_list)

    def test_remove_duplicate_fingerprints(self):
        """Test remove duplicate fingerprints created by index."""
        fingerprints = [
            {'id': 1,
             'os_release': 'RHEL 7',
             'mac_addresses': ['1234', '2345']},
            {'id': 2,
             'os_release': 'RHEL 7',
             'mac_addresses': ['9876', '8765']},
            {'id': 3,
             'os_release': 'RHEL 6'}
        ]
        index, no_key_found = _create_index_for_fingerprint(
            'mac_addresses', fingerprints)

        self.assertEqual(len(no_key_found), 1)
        self.assertEqual(no_key_found[0]['id'], 3)
        self.assertIsNotNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))
        self.assertEqual(len(index.keys()), 4)
        self.assertIsNotNone(index.get('1234'))
        self.assertIsNotNone(index.get('2345'))
        self.assertIsNotNone(index.get('9876'))
        self.assertIsNotNone(index.get('8765'))

        # deplicate but leave unique key
        leave_key_list = list(index.values())
        unique_list = _remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list)
        self.assertEqual(len(unique_list), 2)
        self.assertIsNotNone(unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY))

        # same test, but add value that doesn't have key
        leave_key_list = list(index.values())
        leave_key_list.append({'id': 3, 'os_release': 'RHEL 6'})
        unique_list = _remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], leave_key_list)
        self.assertEqual(len(unique_list), 3)

        # now pass flag to strip id key
        remove_key_list = list(index.values())
        unique_list = _remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], remove_key_list, True)
        self.assertEqual(len(unique_list), 2)
        self.assertIsNone(unique_list[0].get(FINGERPRINT_GLOBAL_ID_KEY))

    def test_create_index_for_fingerprints(self):
        """Test create index for fingerprints."""
        fingerprints = [
            {'id': 1, 'os_release': 'RHEL 7', 'bios_uuid': '1234'},
            {'id': 2, 'os_release': 'RHEL 7', 'bios_uuid': '2345'},
            {'id': 3, 'os_release': 'RHEL 6'}
        ]

        # Test that unique id not in objects
        index, no_key_found = _create_index_for_fingerprint(
            'bios_uuid', fingerprints, False)
        self.assertIsNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))

        # Tests with unique id in objects
        index, no_key_found = _create_index_for_fingerprint(
            'bios_uuid', fingerprints)

        self.assertEqual(len(no_key_found), 1)
        self.assertEqual(no_key_found[0]['id'], 3)
        self.assertIsNotNone(no_key_found[0].get(FINGERPRINT_GLOBAL_ID_KEY))
        self.assertEqual(len(index.keys()), 2)
        self.assertIsNotNone(index.get('1234'))
        self.assertIsNotNone(index.get('2345'))

    def test_merge_fingerprint(self):
        """Test merging a vcenter and network fingerprint."""
        nfingerprint = self._create_network_fingerprint()
        vfingerprint = self._create_vcenter_fingerprint()

        self.assertIsNone(nfingerprint.get('vm_state'))
        self.assertIsNone(nfingerprint.get('vm_uuid'))
        self.assertIsNone(nfingerprint.get('vm_memory_size'))
        self.assertIsNone(nfingerprint.get('vm_dns_name'))
        self.assertIsNone(nfingerprint.get('vm_host_cpu_cores'))
        self.assertIsNone(nfingerprint.get('vm_host_cpu_threads'))
        self.assertIsNone(nfingerprint.get('vm_host_socket_count'))
        self.assertIsNone(nfingerprint.get('vm_datacenter'))
        self.assertIsNone(nfingerprint.get('vm_cluster'))

        self.assertIsNone(vfingerprint.get('os_name'))
        self.assertIsNone(vfingerprint.get('os_version'))
        self.assertIsNone(vfingerprint.get('bios_uuid'))
        self.assertIsNone(vfingerprint.get('subscription_manager_id'))
        self.assertIsNone(vfingerprint.get('cpu_core_per_socket'))
        self.assertIsNone(vfingerprint.get('cpu_siblings'))
        self.assertIsNone(vfingerprint.get('cpu_hyperthreading'))
        self.assertIsNone(vfingerprint.get('cpu_socket_count'))
        self.assertIsNone(vfingerprint.get('cpu_core_count'))

        new_fingerprint = _merge_fingerprint(nfingerprint, vfingerprint)

        self.assertIsNotNone(new_fingerprint.get('vm_state'))
        self.assertIsNotNone(new_fingerprint.get('vm_uuid'))
        self.assertIsNotNone(new_fingerprint.get('vm_memory_size'))
        self.assertIsNotNone(new_fingerprint.get('vm_dns_name'))
        self.assertIsNotNone(new_fingerprint.get('vm_host_cpu_cores'))
        self.assertIsNotNone(new_fingerprint.get('vm_host_cpu_threads'))
        self.assertIsNotNone(new_fingerprint.get('vm_host_socket_count'))
        self.assertIsNotNone(new_fingerprint.get('vm_datacenter'))
        self.assertIsNotNone(new_fingerprint.get('vm_cluster'))

        self.assertIsNotNone(new_fingerprint.get('name'))
        self.assertIsNotNone(new_fingerprint.get('os_name'))
        self.assertIsNotNone(new_fingerprint.get('os_version'))
        self.assertIsNotNone(new_fingerprint.get('bios_uuid'))
        self.assertIsNotNone(new_fingerprint.get('subscription_manager_id'))
        self.assertIsNotNone(new_fingerprint.get('cpu_core_per_socket'))
        self.assertIsNotNone(new_fingerprint.get('cpu_siblings'))
        self.assertIsNotNone(new_fingerprint.get('cpu_hyperthreading'))
        self.assertIsNotNone(new_fingerprint.get('cpu_socket_count'))
        self.assertIsNotNone(new_fingerprint.get('cpu_core_count'))

    def test_merge_fingerprint_network_win(self):
        """Test merge of fingerprint prioritizes network values."""
        nfingerprint = self._create_network_fingerprint()
        vfingerprint = self._create_vcenter_fingerprint()

        nfingerprint['os_release'] = 'Fedora'
        self.assertNotEqual(vfingerprint.get('os_release'),
                            nfingerprint['os_release'])

        new_fingerprint = _merge_fingerprint(nfingerprint, vfingerprint)

        self.assertEqual(new_fingerprint.get(
            'os_release'), nfingerprint['os_release'])
