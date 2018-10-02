#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the fingerprint model."""
from django.test import TestCase

from api.models import FactCollection  # noqa I100
from api.serializers import FingerprintSerializer


class FingerprintModelTest(TestCase):
    """Tests against the Fingerprint model."""

    def setUp(self):
        """Create test case setup."""
        self.fact_collection = FactCollection()
        self.fact_collection.save()

    ################################################################
    # Test Model Create
    ################################################################
    def test_empty_fingerprint(self):
        """Create an empty fingerprint."""
        fingerprint_dict = {'report_id': self.fact_collection.id,
                            'metadata': {},
                            'sources': []}

        serializer = FingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    # pylint: disable=invalid-name
    def test_product_with_version_fingerprint(self):
        """Create a fingerprint with products."""
        product_dict = {'name': 'product1',
                        'presence': 'unknown',
                        'version': ['1', '2'],
                        'metadata': {}}
        fingerprint_dict = {'report_id': self.fact_collection.id,
                            'metadata': {},
                            'products': [product_dict],
                            'sources': []}

        serializer = FingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    def test_product_fingerprint(self):
        """Create a fingerprint with products."""
        product_dict = {'name': 'product1',
                        'presence': 'unknown',
                        'metadata': {}}
        fingerprint_dict = {'report_id': self.fact_collection.id,
                            'metadata': {},
                            'products': [product_dict],
                            'sources': []}

        serializer = FingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()

    def test_entitlement_fingerprint(self):
        """Create a fingerprint with entitlements."""
        entitlement_dict = {'name': 'RHEL Server',
                            'entitlement_id': '69',
                            'metadata': {}}
        fingerprint_dict = {'report_id': self.fact_collection.id,
                            'metadata': {},
                            'entitlements': [entitlement_dict],
                            'sources': []}

        serializer = FingerprintSerializer(data=fingerprint_dict)
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        serializer.save()
