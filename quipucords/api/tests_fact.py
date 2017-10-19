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
"""Test the fact API"""

import uuid
import json
from django.core.urlresolvers import reverse
from django.test import TestCase
from api.fact_model import FactCollection, Fact
from rest_framework import status


class FactCollectionTest(TestCase):
    """ Tests against the FactCollection model and view set"""
    # pylint: disable= no-self-use

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

    def create_json_fc(self, etc_release_name='RHEL',
                       etc_release_release='RHEL 7.4 (Maipo)',
                       etc_release_version='7.4 (Maipo)',
                       connection_uuid=str(uuid.uuid4())):
        """Creates an in memory FactCollection for tests."""

        fact = {'etc_release_name': etc_release_name,
                'etc_release_release': etc_release_release,
                'etc_release_version': etc_release_version,
                'connection_uuid': connection_uuid}
        fact_collection = {'facts': [fact]}
        return fact_collection

    def test_fc_creation(self):
        """ Test model creation not via API."""
        fact_collection = self.create_fc()
        string_value = str(fact_collection)
        self.assertIsInstance(string_value, str)
        self.assertTrue(isinstance(fact_collection, FactCollection))
        self.assertIsInstance(str(fact_collection.facts.all()[0]), str)

    def test_fc_api_create(self):
        """ Create fact collection object via API."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc()
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        json_fact_collection = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            json_fact_collection['facts'], fact_collection['facts'])
        self.assertEqual(FactCollection.objects.count(), 1)

    def test_fc_api_no_facts(self):
        """Ensure error if missing facts array."""

        url = reverse("facts-list")
        response = self.client.post(url, json.dumps({}),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_empty_facts(self):
        """Ensure error if missing facts array."""
        url = reverse("facts-list")
        response = self.client.post(url, json.dumps({'facts': []}),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_missing_name(self):
        """ Missing etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            etc_release_name=None)
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_missing_release(self):
        """ Missing etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            etc_release_release=None)
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_missing_version(self):
        """ Missing etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            etc_release_version=None)
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_missing_conn_uuid(self):
        """ Missing connection_util not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            connection_uuid=None)
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_empty_name(self):
        """ Empty etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(etc_release_name='')
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_empty_release(self):
        """ Empty etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            etc_release_release='')
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_empty_version(self):
        """ Empty etc_release_name not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            etc_release_version='')
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_empty_conn_uuid(self):
        """ Empty connection_uuid not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            connection_uuid='')
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fc_api_invalid_conn_uuid(self):
        """ Empty connection_uuid not allowed."""

        url = reverse("facts-list")
        fact_collection = self.create_json_fc(
            connection_uuid='abc')
        response = self.client.post(url, json.dumps(fact_collection),
                                    'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
