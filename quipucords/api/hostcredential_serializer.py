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
from api.hostcredential_model import HostCredential


def expand_filepath(filepath):
    """Expand the ssh_keyfile filepath if necessary.
    """
    if filepath is not None:
        expanded = os.path.abspath(
            os.path.normpath(
                os.path.expanduser(
                    os.path.expandvars(filepath))))
        return expanded
    return filepath


class HostCredentialSerializer(ModelSerializer):
    """Serializer for the HostCredential model"""
    class Meta:
        model = HostCredential
        fields = '__all__'

    def validate(self, attrs):
        ssh_keyfile = 'ssh_keyfile' in attrs and attrs['ssh_keyfile']
        password = 'password' in attrs and attrs['password']
        if not (password or ssh_keyfile):
            raise ValidationError(_('A host credential must have either'
                                    ' a password or an ssh_keyfile.'))

        if password and ssh_keyfile:
            raise ValidationError(_('A host credential must have either'
                                    ' a password or an ssh_keyfile, not '
                                    'both.'))

        if ssh_keyfile:
            keyfile = expand_filepath(ssh_keyfile)
            if not os.path.isfile(keyfile):
                raise ValidationError(_('ssh_keyfile, %s, is not a valid file'
                                        ' on the system.' % (ssh_keyfile)))
            else:
                attrs['ssh_keyfile'] = keyfile

        return attrs
