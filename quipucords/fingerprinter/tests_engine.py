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
from fingerprinter import (Engine,
                           remove_duplicate_systems)


class EngineTest(TestCase):
    """Tests Engine class."""

    # pylint: disable=no-self-use,too-many-arguments
    # pylint: disable=too-many-locals,too-many-branches,invalid-name
    # pylint: disable=protected-access

    ################################################################
    # Helper function
    ################################################################
    def _create_json_fc(self,
                        fc_id=1,
                        connection_host='1.2.3.4',
                        connection_port=22,
                        connection_uuid='a037f26f-2988-57bd-85d8-de7617a3aab0',
                        cpu_count=2,
                        cpu_core_per_socket=1,
                        cpu_siblings=1,
                        cpu_hyperthreading=False,
                        cpu_socket_count=2,
                        cpu_core_count=2,
                        date_anaconda_log='2017-06-17',
                        date_yum_history='2017-07-18',
                        etc_release_name='RHEL',
                        etc_release_version='7.4 (Maipo)',
                        etc_release_release='RHEL 7.4 (Maipo)',
                        virt_virt='virt-guest',
                        virt_type='vmware',
                        virt_num_guests=1,
                        virt_num_running_guests=1,
                        virt_what_type='vt'):
        """Create an in memory FactCollection for tests."""
        fact = {}
        if connection_host:
            fact['connection_host'] = connection_host
        if connection_port:
            fact['connection_port'] = connection_port
        if connection_uuid:
            fact['connection_uuid'] = connection_uuid
        if cpu_count:
            fact['cpu_count'] = cpu_count
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
        if etc_release_name:
            fact['etc_release_name'] = etc_release_name
        if etc_release_version:
            fact['etc_release_version'] = etc_release_version
        if etc_release_release:
            fact['etc_release_release'] = etc_release_release
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

        fact_collection = {'id': fc_id, 'facts': [fact]}
        return fact_collection

    def test_basic_engine_process_facts(self):
        """Test basic engine process_facts."""
        engine = Engine()
        fact_collection = self._create_json_fc()
        fact = fact_collection['facts'][0]
        fingerprints = engine._process_facts(fact_collection['id'],
                                             1,
                                             fact_collection['facts'])
        fingerprint = fingerprints[0]
        self.validate_result(fingerprint, fact)

    def test_basic_engine_process_fact(self):
        """Test basic engine process_fact."""
        engine = Engine()
        fact_collection = self._create_json_fc()
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.validate_result(fingerprint, fact)

    def test_create_yum(self):
        """Test date_yum_history used for sys create time."""
        engine = Engine()
        fact_collection = self._create_json_fc(date_yum_history='2015-07-18')
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        fact_date = datetime.strptime(fact['date_yum_history'], '%Y-%m-%d')
        fact_date = fact_date.date()
        self.assertEqual(fact_date, fingerprint['system_creation_date'])

    def test_infrastructure_baremetal(self):
        """Test virt_what_type set to bare metal."""
        engine = Engine()
        fact_collection = self._create_json_fc(virt_what_type='bare metal')
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertEqual('bare_metal', fingerprint['infrastructure_type'])

    def test_infrastructure_unknown(self):
        """Test virt_what_type not bear metal.

        virt_type None yields unknown infrastructure type
        """
        engine = Engine()
        fact_collection = self._create_json_fc(
            virt_what_type='foobar', virt_type=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertEqual('unknown', fingerprint['infrastructure_type'])

    def test_infrastructure_missing(self):
        """Test missing virt_what_type and virt_type yields unknown type."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            virt_what_type=None, virt_type=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertEqual('unknown', fingerprint['infrastructure_type'])

    # Test missing fields
    def test_os_name_missing(self):
        """Test missing etc_release_name."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            etc_release_name=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('os_name', fingerprint)

    def test_os_version_missing(self):
        """Test missing etc_release_version."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            etc_release_version=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('os_version', fingerprint)

    def test_os_release_missing(self):
        """Test missing etc_release_release."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            etc_release_release=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('os_release', fingerprint)

    def test_connection_uuid_missing(self):
        """Test missing connection_uuid."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            connection_uuid=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('connection_uuid', fingerprint)

    def test_connection_host_missing(self):
        """Test missing connection_host."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            connection_host=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('connection_host', fingerprint)

    def test_connection_port_missing(self):
        """Test missing connection_port."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            connection_port=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('connection_port', fingerprint)

    def test_cpu_count_missing(self):
        """Test missing cpu_count."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_count=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_count', fingerprint)

    def test_cpu_core_per_socket_missing(self):
        """Test missing cpu_core_per_socket."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_core_per_socket=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_core_per_socket', fingerprint)

    def test_cpu_siblings_missing(self):
        """Test missing cpu_siblings."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_siblings=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_siblings', fingerprint)

    def test_cpu_hyperthreading_missing(self):
        """Test missing cpu_hyperthreading."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_hyperthreading=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_hyperthreading', fingerprint)

    def test_cpu_socket_count_missing(self):
        """Test missing cpu_socket_count."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_socket_count=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_socket_count', fingerprint)

    def test_cpu_core_count_missing(self):
        """Test missing connection_port."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            cpu_core_count=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('cpu_core_count', fingerprint)

    def test_virt_type_missing(self):
        """Test missing virt_type."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            virt_type=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('virtualization_type', fingerprint)

    def test_virt_num_guests_missing(self):
        """Test missing virt_num_guests."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            virt_num_guests=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('virtualization_num_guests', fingerprint)

    def test_virt_num_running_guests_missing(self):
        """Test missing virt_num_running_guests."""
        engine = Engine()
        fact_collection = self._create_json_fc(
            virt_num_running_guests=None)
        fact = fact_collection['facts'][0]
        fingerprint = engine._process_fact(fact)
        self.assertNotIn('virtualization_num_running_guests', fingerprint)

    def validate_result(self, fingerprint, fact):
        """Help to validate fields."""
        self.assertEqual(fact['etc_release_name'], fingerprint['os_name'])
        self.assertEqual(fact['etc_release_release'],
                         fingerprint['os_release'])
        self.assertEqual(fact['etc_release_version'],
                         fingerprint['os_version'])

        self.assertEqual(fact['connection_host'],
                         fingerprint['connection_host'])
        self.assertEqual(fact['connection_port'],
                         fingerprint['connection_port'])
        self.assertEqual(fact['connection_uuid'],
                         fingerprint['connection_uuid'])

        self.assertEqual(fact['cpu_count'], fingerprint['cpu_count'])
        self.assertEqual(fact['cpu_core_per_socket'],
                         fingerprint['cpu_core_per_socket'])
        self.assertEqual(fact['cpu_siblings'], fingerprint['cpu_siblings'])
        self.assertEqual(fact['cpu_hyperthreading'],
                         fingerprint['cpu_hyperthreading'])
        self.assertEqual(fact['cpu_socket_count'],
                         fingerprint['cpu_socket_count'])
        self.assertEqual(fact['cpu_core_count'], fingerprint['cpu_core_count'])

        fact_date = datetime.strptime(fact['date_anaconda_log'], '%Y-%m-%d')
        fact_date = fact_date.date()

        self.assertEqual(fact_date, fingerprint['system_creation_date'])
        self.assertEqual('virtualized', fingerprint['infrastructure_type'])
        self.assertTrue(fingerprint['virtualized_is_guest'])

        self.assertEqual(fact['virt_type'], fingerprint['virtualized_type'])
        self.assertEqual(fact['virt_num_guests'],
                         fingerprint['virtualized_num_guests'])
        self.assertEqual(fact['virt_num_running_guests'],
                         fingerprint['virtualized_num_running_guests'])

    def test_remove_duplicate_systems_one_key(self):
        """Test removing duplicates with one id key."""
        system1 = {'id': 1,
                   'key1': 'value1',
                   'key2': 'value2',
                   'always_unique': 1}
        system2 = {'id': 2,
                   'key1': 'value1',
                   'key2': 'value2',
                   'always_unique': 2}
        systems = [system1, system2]
        unique_systems = remove_duplicate_systems(systems, ['always_unique'])
        self.assertEqual(len(unique_systems), 2)

        unique_systems = remove_duplicate_systems(systems, ['key1'])
        self.assertEqual(len(unique_systems), 1)

    def test_remove_duplicate_systems_two_key(self):
        """Test removing duplicates with two id keys."""
        system1 = {'id': 1,
                   'key1': '1and2',
                   'key2': 'value1'}
        system2 = {'id': 2,
                   'key1': '1and2',
                   'key2': '2and3'}
        system3 = {'id': 3,
                   'key1': 'value3',
                   'key2': '2and3'}
        systems = [system1, system2, system3]

        unique_systems = remove_duplicate_systems(systems, ['key1'])
        self.assertEqual(len(unique_systems), 2)

        unique_systems = remove_duplicate_systems(systems, ['key2'])
        self.assertEqual(len(unique_systems), 2)

        unique_systems = remove_duplicate_systems(systems, ['key1', 'key2'])
        self.assertEqual(len(unique_systems), 1)

    def test_remove_duplicate_systems_none_key_values(self):
        """Test removing duplicates when system missing id key."""
        system1 = {'id': 1,
                   'key1': '1and2',
                   'key2': 'value1'}
        system2 = {'id': 2,
                   'key1': '1and2'}
        system3 = {'id': 3}
        systems = [system1, system2, system3]

        unique_systems = remove_duplicate_systems(systems, ['key1'])
        self.assertEqual(len(unique_systems), 2)

        unique_systems = remove_duplicate_systems(systems, ['key2'])
        self.assertEqual(len(unique_systems), 3)

        unique_systems = remove_duplicate_systems(
            systems, ['id', 'key1', 'key2'])
        self.assertEqual(len(unique_systems), 2)
