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

import yaml
from django.test import TestCase
from . import vault


class VaultTest(TestCase):
    """Tests against the vault class"""

    def test_encrypt_data_as_unicode(self):
        """Tests the encryption of sensitive data using SECRET_KEY"""
        value = vault.encrypt_data_as_unicode('encrypted data')
        self.assertTrue(isinstance(value, str))

    def test_decrypt_data(self):
        """Test the decryption of data using SECRET_KEY"""
        raw = 'encrypted data'
        encrypted = vault.encrypt_data_as_unicode(raw)
        decrypted = vault.decrypt_data_as_unicode(encrypted)
        self.assertEqual(raw, decrypted)

    def test_dump_yaml(self):
        """Test the writing of dictionary data to a yaml file encrypted
        via the vault
        """
        data = {'all': {'hosts': {'1.2.3.4': None},
                        'vars': {'ansible_port': 22,
                                 'ansible_ssh_pass': 'password',
                                 'ansible_user': 'username'}}}
        temp_yaml = vault.write_to_yaml(data)
        self.assertTrue('yaml' in temp_yaml)

        with open(temp_yaml, 'r') as temp_file:
            encrypted = temp_file.read()
            decrypted = vault.decrypt_data_as_unicode(encrypted)
            obj = yaml.load(decrypted)
            self.assertEqual(obj, data)
