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
""" Vault is used to read and write data securely using the Ansible vault """

from django.conf import settings
from ansible.parsing.vault import VaultLib


def encrypt_data(data):
    """Encrypt the incoming data using SECRET_KEY

    :param data: string data to be encrypted
    :returns: vault encrypted data as binary
    """
    vault = Vault(settings.SECRET_KEY)
    return vault.dump(data)


def encrypt_data_as_unicode(data):
    """Encrypt data and return as unicode string

    :param data: string data to be encrypted
    :returns: unicode string of encrypted data using vault
    """
    return encrypt_data(data).decode('utf-8')


# pylint: disable=too-few-public-methods
class Vault(object):
    """ Read and write data using the Ansible vault"""

    def __init__(self, password):
        self.password = password
        self.vault = VaultLib(password)

    def dump(self, data, stream=None):
        """ Encrypt data and print stdout or write to stream

        :param data: The information to be encrypted
        :param stream: If not None the location to write the encrypted data to.
        :returns: If stream is None then the encrypted bytes otherwise None.
        """
        encrypted = self.vault.encrypt(data)
        if stream:
            stream.write(encrypted)
        else:
            return encrypted
