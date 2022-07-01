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
"""Module for serializing all model object for database storage."""

import os

from api import messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.common.util import check_for_existing_name
from api.models import Credential

from django.utils.translation import ugettext as _

from rest_framework.serializers import (CharField,
                                        ValidationError)


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

    name = CharField(required=True, max_length=64)
    cred_type = ValidStringChoiceField(
        required=False, choices=Credential.CRED_TYPE_CHOICES)
    username = CharField(required=True, max_length=64)
    password = CharField(required=False, max_length=1024, allow_null=True,
                         style={'input_type': 'password'})
    ssh_keyfile = CharField(required=False, max_length=1024, allow_null=True)
    ssh_passphrase = CharField(required=False, max_length=1024,
                               allow_null=True,
                               style={'input_type': 'password'})
    become_method = ValidStringChoiceField(
        required=False, choices=Credential.BECOME_METHOD_CHOICES)
    become_user = CharField(required=False, max_length=64)
    become_password = CharField(required=False, max_length=1024,
                                allow_null=True,
                                style={'input_type': 'password'})

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = '__all__'

    def create(self, validated_data):
        """Create host credential."""
        name = validated_data.get('name')
        check_for_existing_name(
            Credential.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name))

        if 'cred_type' not in validated_data:
            error = {
                'cred_type': [_(messages.CRED_TYPE_REQUIRED_CREATED)]
            }
            raise ValidationError(error)

        cred_type = validated_data.get('cred_type')
        become_method = validated_data.get('become_method')
        become_user = validated_data.get('become_user')

        if cred_type == Credential.NETWORK_CRED_TYPE and not become_method:
            # Set the default become_method to be sudo if not specified
            validated_data['become_method'] = Credential.BECOME_SUDO
        if cred_type == Credential.NETWORK_CRED_TYPE and not become_user:
            # Set the default become_user to root if not specified
            validated_data['become_user'] = Credential.BECOME_USER_DEFAULT

        if cred_type == Credential.VCENTER_CRED_TYPE:
            validated_data = self.validate_vcenter_cred(validated_data)
        elif cred_type == Credential.SATELLITE_CRED_TYPE:
            validated_data = self.validate_satellite_cred(validated_data)
        else:
            validated_data = self.validate_host_cred(validated_data)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a host credential."""
        name = validated_data.get('name')
        check_for_existing_name(
            Credential.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name),
            search_id=instance.id)

        if 'cred_type' in validated_data:
            error = {
                'cred_type': [_(messages.CRED_TYPE_NOT_ALLOWED_UPDATE)]
            }
            raise ValidationError(error)

        cred_type = instance.cred_type
        if cred_type == Credential.VCENTER_CRED_TYPE:
            validated_data = self.validate_vcenter_cred(validated_data)
        elif cred_type == Credential.SATELLITE_CRED_TYPE:
            validated_data = self.validate_satellite_cred(validated_data)
        else:
            validated_data = self.validate_host_cred(validated_data)

        return super().update(instance, validated_data)

    def validate_host_cred(self, attrs):
        """Validate the attributes for host creds."""
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        password = 'password' in attrs and attrs['password']
        ssh_passphrase = 'ssh_passphrase' in attrs and attrs['ssh_passphrase']
        if not (password or ssh_keyfile) and not self.partial:
            error = {
                'non_field_errors': [_(messages.HC_PWD_OR_KEYFILE)]
            }
            raise ValidationError(error)

        if password and ssh_keyfile:
            error = {
                'non_field_errors': [_(messages.HC_NOT_BOTH)]
            }
            raise ValidationError(error)

        if ssh_keyfile:
            keyfile = expand_filepath(ssh_keyfile)
            if not os.path.isfile(keyfile):
                error = {
                    'ssh_keyfile': [_(messages.HC_KEY_INVALID
                                      % (ssh_keyfile))]
                }
                raise ValidationError(error)
            attrs['ssh_keyfile'] = keyfile

        if ssh_passphrase and not ssh_keyfile and not self.partial:
            error = {
                'ssh_passphrase': [_(messages.HC_NO_KEY_W_PASS)]
            }
            raise ValidationError(error)

        return attrs

    def validate_vcenter_cred(self, attrs):
        """Validate the attributes for vcenter creds."""
        # Required fields for vcenter
        if not self.partial:
            username = 'username' in attrs and attrs['username']
            password = 'password' in attrs and attrs['password']

            if not (password and username):
                error = {
                    'non_field_errors': [_(messages.VC_PWD_AND_USERNAME)]
                }
                raise ValidationError(error)

        # Not allowed fields for vcenter
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        ssh_passphrase = 'ssh_passphrase' in attrs\
                         and attrs['ssh_passphrase']
        become_password = 'become_password' in attrs \
                          and attrs['become_password']
        become_user = 'become_user' in attrs and attrs['become_user']
        become_method = 'become_method' in attrs \
                        and attrs['become_method']

        if ssh_keyfile or ssh_passphrase or become_password or \
                become_user or become_method:
            error = {
                'non_field_errors': [_(messages.VC_FIELDS_NOT_ALLOWED)]
            }
            raise ValidationError(error)

        return attrs

    def validate_satellite_cred(self, attrs):
        """Validate the attributes for satellite creds."""
        # Required fields for satellite
        if not self.partial:
            username = 'username' in attrs and attrs['username']
            password = 'password' in attrs and attrs['password']

            if not (password and username):
                error = {
                    'non_field_errors': [_(messages.SAT_PWD_AND_USERNAME)]
                }
                raise ValidationError(error)

        # Not allowed fields for satellite
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        ssh_passphrase = 'ssh_passphrase' in attrs \
            and attrs['ssh_passphrase']
        become_password = 'become_password' in attrs \
            and attrs['become_password']
        become_user = 'become_user' in attrs and attrs['become_user']
        become_method = 'become_method' in attrs \
                        and attrs['become_method']

        if ssh_keyfile or ssh_passphrase or become_password or \
                become_user or become_method:
            error = {
                'non_field_errors': [_(messages.SAT_FIELDS_NOT_ALLOWED)]
            }
            raise ValidationError(error)
        return attrs
