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
"""Test the API application"""

from django.test import TestCase
from . import vault


class VaultTest(TestCase):
    """Tests against the vault class"""

    def test_encrypt_data_as_unicode(self):
        """Tests the encryption of sensitive data using SECRET_KEY"""
        value = vault.encrypt_data_as_unicode('encrypted data')
        self.assertTrue(isinstance(value, str))
