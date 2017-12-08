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
"""Module for serializing all model object for database storage."""

import os
from django.utils.translation import ugettext as _
from rest_framework.serializers import (ValidationError,
                                        ChoiceField,
                                        CharField)
from api.models import Credential
import api.messages as messages
from api.common.serializer import NotEmptySerializer


def expand_filepath(filepath):
    """Expand the ssh_keyfile filepath if necessary."""
    if filepath is not None:
        expanded = os.path.abspath(
            os.path.normpath(
                os.path.expanduser(
                    os.path.expandvars(filepath))))
        return expanded
    return filepath


class CredentialSerializer(NotEmptySerializer):
    """Serializer for the Credential model."""

    # pylint: disable= no-self-use

    name = CharField(required=True, max_length=64)
    cred_type = ChoiceField(
        required=False, choices=Credential.CRED_TYPE_CHOICES)
    username = CharField(required=True, max_length=64)
    password = CharField(required=False, max_length=1024, allow_null=True,
                         style={'input_type': 'password'})
    sudo_password = CharField(required=False, max_length=1024, allow_null=True,
                              style={'input_type': 'password'})
    ssh_keyfile = CharField(required=False, max_length=1024, allow_null=True)
    ssh_passphrase = CharField(required=False, max_length=1024,
                               allow_null=True,
                               style={'input_type': 'password'})

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = '__all__'

    def create(self, validated_data):
        """Create host credential."""
        CredentialSerializer.check_for_existing_name(
            name=validated_data.get('name'))

        if 'cred_type' not in validated_data:
            raise ValidationError(_(messages.CRED_TYPE_REQUIRED_CREATED))

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a host credential."""
        CredentialSerializer.check_for_existing_name(
            name=validated_data.get('name'),
            cred_id=instance.id)

        if 'cred_type' in validated_data:
            raise ValidationError(_(messages.CRED_TYPE_NOT_ALLOWED_UPDATE))

        return super().update(instance, validated_data)

    @staticmethod
    def check_for_existing_name(name, cred_id=None):
        """Look for existing (different object) with same name.

        :param name: Name of credential to look for
        :param cred_id: Host credential to exclude
        """
        if cred_id is None:
            # Look for existing with same name (create)
            existing = Credential.objects.filter(name=name).first()
        else:
            # Look for existing.  Same name, different id (update)
            existing = Credential.objects.filter(
                name=name).exclude(id=cred_id).first()
        if existing is not None:
            raise ValidationError(_(messages.HC_NAME_ALREADY_EXISTS % name))

    def validate(self, attrs):
        """Validate the attributes."""
        cred_type = 'cred_type' in attrs and attrs['cred_type']
        if cred_type == Credential.VCENTER_CRED_TYPE:
            return self.validate_vcenter_cred(attrs)
        return self.validate_host_cred(attrs)

    def validate_host_cred(self, attrs):
        """Validate the attributes for host creds."""
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        password = 'password' in attrs and attrs['password']
        ssh_passphrase = 'ssh_passphrase' in attrs and attrs['ssh_passphrase']
        if not (password or ssh_keyfile):
            raise ValidationError(_(messages.HC_PWD_OR_KEYFILE))

        if password and ssh_keyfile:
            raise ValidationError(_(messages.HC_NOT_BOTH))

        if ssh_keyfile:
            keyfile = expand_filepath(ssh_keyfile)
            if not os.path.isfile(keyfile):
                raise ValidationError(_(messages.HC_KEY_INVALID
                                        % (ssh_keyfile)))
            else:
                attrs['ssh_keyfile'] = keyfile

        if ssh_passphrase and not ssh_keyfile:
            raise ValidationError(_(messages.HC_NO_KEY_W_PASS))
        return attrs

    def validate_vcenter_cred(self, attrs):
        """Validate the attributes for vcenter creds."""
        # Required fields for vcenter
        username = 'username' in attrs and attrs['username']
        password = 'password' in attrs and attrs['password']

        if not (password and username):
            raise ValidationError(_(messages.VC_PWD_AND_USERNAME))

        # Not allowed fields for vcenter
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        ssh_passphrase = 'ssh_passphrase' in attrs and attrs['ssh_passphrase']
        sudo_password = 'sudo_password' in attrs and attrs['sudo_password']

        if ssh_keyfile or ssh_passphrase or sudo_password:
            raise ValidationError(_(messages.VC_KEY_FILE_NOT_ALLOWED))

        return attrs
