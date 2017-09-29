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
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework.serializers import ModelSerializer, ValidationError, \
    SlugRelatedField
from api.models import Credential, HostCredential, HostRange, NetworkProfile


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


class HostRangeField(SlugRelatedField):
    # SlugRelatedField is *almost* what we want for HostRanges, but it
    # doesn't allow creating new HostRanges because it requires them
    # to already exist or else to_internal_value raises a
    # ValidationError, and Serializer.is_valid() will call
    # to_internal_value() before it calls our custom create() method.

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise ValidationError('A host range must be a string.')

        return {'host_range': data}


class NetworkProfileSerializer(ModelSerializer):
    """Serializer for the NetworkProfile model"""

    hosts = HostRangeField(
        many=True,
        slug_field='host_range',
        queryset=HostRange.objects.all())

    class Meta:
        model = NetworkProfile
        fields = '__all__'

    # Have to implement explicit create() and update() methods to
    # allow creates/updates of nested HostRange field. See
    # http://www.django-rest-framework.org/api-guide/relations/
    @transaction.atomic
    def create(self, validated_data):
        hosts_data = validated_data.pop('hosts')
        credentials = validated_data.pop('credentials')

        netprof = NetworkProfile.objects.create(**validated_data)

        for host_data in hosts_data:
            HostRange.objects.create(network_profile=netprof,
                                     **host_data)

        for cred_id in credentials:
            netprof.credentials.add(cred_id)

        return netprof

    @transaction.atomic
    def update(self, instance, validated_data):
        # If we ever add optional fields to NetworkProfile, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.

        hosts_data = validated_data.pop('hosts', None)
        credentials = validated_data.pop('credentials', None)

        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()

        # If hosts_data was not supplied and this is a full update,
        # then we should already have raised a ValidationError before
        # this point, so it's safe to use hosts_data as an indicator
        # of whether to replace the hosts.
        if hosts_data:
            new_hosts = [
                HostRange.objects.create(network_profile=instance,
                                         **host_data)
                for host_data in hosts_data]
            instance.hosts.set(new_hosts)

        # credentials is safe to use as a flag for the same reason as
        # hosts_data above.
        if credentials:
            instance.credentials.set(credentials)

        return instance

    @staticmethod
    def validate_name(name):
        """Validate the name of the NetworkProfile."""
        if not isinstance(name, str) or not name.isprintable():
            raise ValidationError('NetworkProfile must have printable name.')

        return name

    @staticmethod
    def validate_hosts(hosts):
        """Make sure the hosts list is present."""
        if not hosts:
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
        """Make sure the credentials list is present."""
        if not credentials:
            raise ValidationError('NetworkProfile must have at least one set '
                                  'of credentials.')

        return credentials
