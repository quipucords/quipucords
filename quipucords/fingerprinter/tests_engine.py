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

    def create_json_fc(self, fc_id=1, etc_release_name='RHEL',
                       etc_release_release='RHEL 7.4 (Maipo)',
                       etc_release_version='7.4 (Maipo)',
                       connection_uuid=str(uuid.uuid4())):
        """Creates an in memory FactCollection for tests."""

        fact = {'etc_release_name': etc_release_name,
                'etc_release_release': etc_release_release,
                'etc_release_version': etc_release_version,
                'connection_uuid': connection_uuid}
        fact_collection = {'id': fc_id, 'facts': [fact]}
        return fact_collection

    def create_fc(self, etc_release_name='RHEL',
                  etc_release_release='RHEL 7.4 (Maipo)',
                  etc_release_version='7.4 (Maipo)',
                  connection_uuid=str(uuid.uuid4())):
        """Creates a FactCollection model for use within test cases

        :param etc_release_name: name of the release
        :param etc_release_release: the release string
        :param etc_release_version: the version of the release
        :returns: A FactCollection model
        """
        fact = Fact.objects.create(etc_release_name=etc_release_name,
                                   etc_release_release=etc_release_release,
                                   etc_release_version=etc_release_version,
                                   connection_uuid=connection_uuid)
        fact_collection = FactCollection.objects.create()
        fact_collection.facts.add(fact)
        fact_collection.save()
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
