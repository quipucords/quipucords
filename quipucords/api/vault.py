"""Vault is used to read and write data securely using the Ansible vault."""

import tempfile

import yaml

# ANSIBLE API DEPENDENCY
from ansible.module_utils._text import to_bytes
from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.parsing.yaml.dumper import AnsibleDumper
from django.conf import settings


def represent_none(self, _):
    """Render None with nothing in yaml string when dumped."""
    return self.represent_scalar("tag:yaml.org,2002:null", "")


yaml.add_representer(type(None), represent_none)


def encrypt_data(data):
    """Encrypt the incoming data using SECRET_KEY.

    :param data: string data to be encrypted
    :returns: vault encrypted data as binary
    """
    vault = Vault(settings.QUIPUCORDS_ENCRYPTION_SECRET_KEY)
    return vault.dump(data)


def decrypt_data(data):
    """Decrypt the incoming data using SECRET_KEY.

    :param data: string data to be decrypted
    :returns: vault decrypted data as string
    """
    vault = Vault(settings.QUIPUCORDS_ENCRYPTION_SECRET_KEY)
    return vault.load(data)


def encrypt_data_as_unicode(data):
    """Encrypt data and return as unicode string.

    :param data: string data to be encrypted
    :returns: unicode string of encrypted data using vault
    """
    if "$ANSIBLE_VAULT" in data:
        return data
    return encrypt_data(data).decode("utf-8")


def decrypt_data_as_unicode(data):
    """Decrypt data and return as unicode string.

    :param data: string data to be decrypted
    :returns: unicode string of decrypted data using vault
    """
    if "$ANSIBLE_VAULT" not in data:
        return data
    return decrypt_data(data).decode("utf-8")


def write_to_yaml(data):
    """Write data to temp yaml file and return the file."""
    vault = Vault(settings.QUIPUCORDS_ENCRYPTION_SECRET_KEY)
    return vault.dump_as_yaml_to_tempfile(data)


class Vault:
    """Read and write data using the Ansible vault."""

    def __init__(self, password):
        """Create a vault."""
        self.password = password
        pass_bytes = to_bytes(password, encoding="utf-8", errors="strict")
        secrets = [("password", VaultSecret(_bytes=pass_bytes))]

        self.vault = VaultLib(secrets=secrets)

    def dump(self, data, stream=None):
        """Encrypt data and print stdout or write to stream.

        :param data: The information to be encrypted
        :param stream: If not None the location to write the encrypted data to.
        :returns: If stream is None then the encrypted bytes otherwise None.
        """
        encrypted = self.vault.encrypt(data)
        if stream:
            stream.write(encrypted)
        else:
            return encrypted

    def load(self, stream):
        """Read vault steam and return python object.

        :param stream: The stream to read data from
        :returns: The decrypted data
        """
        return self.vault.decrypt(stream)

    def dump_as_yaml(self, obj, stream=None):
        """Convert object to yaml and encrypt the data.

        :param obj: Python object to convert to yaml
        :param stream: If not None the location to write the encrypted data to.
        :returns: If stream is None then the encrypted bytes otherwise None.
        """
        data = yaml.dump(
            obj, allow_unicode=True, default_flow_style=False, Dumper=AnsibleDumper
        )
        return self.dump(data, stream)

    def dump_as_yaml_to_tempfile(self, obj):
        """Convert object to yaml and encrypt the data.

        :param obj: Python object to convert to yaml
        :returns: The filepath to write data
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as data_temp:
            self.dump_as_yaml(obj, data_temp)
        data_temp.close()
        return data_temp.name
