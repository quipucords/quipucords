"""Test the API application."""

from pathlib import Path

import yaml
from django.test import TestCase

from api import vault


class VaultTest(TestCase):
    """Tests against the vault class."""

    def test_encrypt_data_as_unicode(self):
        """Tests the encryption of sensitive data using SECRET_KEY."""
        value = vault.encrypt_data_as_unicode("encrypted data")
        self.assertTrue(isinstance(value, str))

    def test_decrypt_data(self):
        """Test the decryption of data using SECRET_KEY."""
        raw = "encrypted data"
        encrypted = vault.encrypt_data_as_unicode(raw)
        decrypted = vault.decrypt_data_as_unicode(encrypted)
        self.assertEqual(raw, decrypted)

    def test_dump_yaml(self):
        """Test the writing of dictionary data to a yaml file encrypted."""
        data = {
            "all": {
                "hosts": {"1.2.3.4": None},
                "vars": {
                    "ansible_port": 22,
                    "ansible_ssh_pass": "password",
                    "ansible_user": "username",
                },
            }
        }
        temp_yaml = Path(vault.write_to_yaml(data))
        assert temp_yaml.name.endswith(".yaml")

        with temp_yaml.open("r", encoding="utf-8") as temp_file:
            encrypted = temp_file.read()
            decrypted = vault.decrypt_data_as_unicode(encrypted)
            obj = yaml.load(decrypted, Loader=yaml.SafeLoader)
            self.assertEqual(obj, data)
