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
"""Module for serializing all model object for database storage"""

import os
from django.utils.translation import ugettext as _
from rest_framework.serializers import ModelSerializer, ValidationError
from api.models import Credential, HostCredential, NetworkProfile


class CredentialSerializer(ModelSerializer):
    """Serializer for the Credential model"""
    class Meta:
        model = Credential
        fields = '__all__'


class HostCredentialSerializer(ModelSerializer):
    """Serializer for the HostCredential model"""
    class Meta:
        model = HostCredential
        fields = '__all__'

    def validate(self, attrs):
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        password = 'password' in attrs and attrs['password']
        if not (password or ssh_keyfile):
            raise ValidationError(_('A host credential must have either' +
                                    ' a password or an ssh_keyfile.'))
        if ssh_keyfile and not os.path.isfile(ssh_keyfile):
            raise ValidationError(_('ssh_keyfile, %s, is not a valid file'
                                    ' on the system.' % (ssh_keyfile)))
        return attrs


class NetworkProfileSerializer(ModelSerializer):
    """Serializer for the NetworkProfile model"""
    class Meta:
        model = NetworkProfile
        fields = '__all__'

    @staticmethod
    def validate_name(name):
        """Validate the name of the NetworkProfile."""
        if not isinstance(name, str) or not name.isprintable():
            raise ValidationError('NetworkProfile must have printable name.')

        return name

    @staticmethod
    def validate_hosts(hosts):
        """Make sure the hosts list is reasonable."""
        host_parts = hosts.split(',')
        if not host_parts:
            raise ValidationError('NetworkProfile must have at least one '
                                  'host.')

        return hosts

    @staticmethod
    def validate_ssh_port(ssh_port):
        """validate the ssh port."""
        if not ssh_port or ssh_port < 0 or ssh_port > 65536:
            raise ValidationError('NetworkProfile must have ssh port in range '
                                  '[0, 65535]')

        return ssh_port

    @staticmethod
    def validate_credentials(credentials):
        """Make sure the credentials list is there."""
        if not credentials:
            raise ValidationError('NetworkProfile must have at least one set '
                                  'of credentials.')

        return credentials
