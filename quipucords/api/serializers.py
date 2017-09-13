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
from api.models import Credential, HostCredential


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
        ssh_keyfile = None
        password = None
        key_ssh_keyfile = 'ssh_keyfile'
        key_password = 'password'
        in_attrs_ssh_keyfile = key_ssh_keyfile in attrs
        in_attrs_password = key_password in attrs
        if in_attrs_ssh_keyfile or in_attrs_password:
            if in_attrs_ssh_keyfile:
                ssh_keyfile = attrs[key_ssh_keyfile]
            if in_attrs_password:
                password = attrs[key_password]
        if password is None and ssh_keyfile is None:
            raise ValidationError(_('A host credential must have either' +
                                    ' a password or an ssh_keyfile.'))
        if ssh_keyfile is not None and not os.path.isfile(ssh_keyfile):
            raise ValidationError(_('ssh_keyfile, %s, is not a valid file'
                                    ' on the system.' % (ssh_keyfile)))
        return attrs
