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

import uuid
from django.test import TestCase
from api.models import Fact, FactCollection
from fingerprinter import Engine


class EngineTest(TestCase):
    """Tests Engine class"""
    # pylint: disable= no-self-use, too-many-arguments

    ################################################################
    # Helper function
    ################################################################
    def create_json_fc(self,
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
                       date_anaconda_log='2017-07-18',
                       date_yum_history='2017-07-18',
                       etc_release_name='RHEL',
                       etc_release_version='7.4 (Maipo)',
                       etc_release_release='RHEL 7.4 (Maipo)',
                       virt_virt='virt-guest',
                       virt_type='vmware',
                       virt_num_guests=1,
                       virt_num_running_guests=1,
                       virt_what_type='vt'):
        """Creates an in memory FactCollection for tests."""

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
        """ Test basic engine process_facts."""
        engine = Engine()
        fact_collection = self.create_json_fc()
        fact = fact_collection['facts'][0]
        fingerprints = engine.process_facts(fact_collection['id'],
                                            fact_collection['facts'])
        fingerprint = fingerprints[0]
        self.assertEqual(fact_collection['id'],
                         fingerprint['fact_collection_id'])
        self.assertEqual(fact['etc_release_name'], fingerprint['os_name'])
        self.assertEqual(fact['etc_release_release'],
                         fingerprint['os_release'])
        self.assertEqual(fact['etc_release_version'],
                         fingerprint['os_version'])

    def test_basic_engine_process_fact(self):
        """ Test basic engine process_fact."""
        engine = Engine()
        fact_collection = self.create_json_fc()
        fact = fact_collection['facts'][0]
        fingerprint = engine.process_fact(fact_collection['id'], fact)
        self.assertEqual(fact_collection['id'],
                         fingerprint['fact_collection_id'])
        self.assertEqual(fact['etc_release_name'], fingerprint['os_name'])
        self.assertEqual(fact['etc_release_release'],
                         fingerprint['os_release'])
        self.assertEqual(fact['etc_release_version'],
                         fingerprint['os_version'])
