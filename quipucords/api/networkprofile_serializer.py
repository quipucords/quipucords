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

from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework.serializers import ModelSerializer, ValidationError, \
    SlugRelatedField, PrimaryKeyRelatedField
from api.hostcredential_model import HostCredential
from api.networkprofile_model import HostRange, NetworkProfile


class HostRangeField(SlugRelatedField):
    """Representation of the host range with in a network profile
    """
    # SlugRelatedField is *almost* what we want for HostRanges, but it
    # doesn't allow creating new HostRanges because it requires them
    # to already exist or else to_internal_value raises a
    # ValidationError, and Serializer.is_valid() will call
    # to_internal_value() before it calls our custom create() method.

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise ValidationError('A host range must be a string.')

        return {'host_range': data}

    def display_value(self, instance):
        return instance.host_range


class CredentialsField(PrimaryKeyRelatedField):
    """Representation of the credentials associated with a network profile
    """
    def to_internal_value(self, data):
        return HostCredential.objects.get(pk=data)

    def to_representation(self, value):
        return value.id

    def display_value(self, instance):
        display = instance
        if isinstance(instance, HostCredential):
            display = 'Credential: %s' % instance.name
        return display


class NetworkProfileSerializer(ModelSerializer):
    """Serializer for the NetworkProfile model"""

    hosts = HostRangeField(
        many=True,
        slug_field='host_range',
        queryset=HostRange.objects.all())

    credentials = CredentialsField(
        many=True,
        queryset=HostCredential.objects.all())

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

        for credential in credentials:
            netprof.credentials.add(credential)

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
            old_hosts = list(instance.hosts.all())
            new_hosts = [
                HostRange.objects.create(network_profile=instance,
                                         **host_data)
                for host_data in hosts_data]
            instance.hosts.set(new_hosts)
            for host in old_hosts:
                host.delete()

        # credentials is safe to use as a flag for the same reason as
        # hosts_data above.
        if credentials:
            instance.credentials.set(credentials)

        return instance

    @staticmethod
    def validate_name(name):
        """Validate the name of the NetworkProfile."""
        if not isinstance(name, str) or not name.isprintable():
            raise ValidationError(_('Network profile must have printable'
                                    ' name.'))

        return name

    @staticmethod
    def validate_hosts(hosts):
        """Make sure the hosts list is present."""
        if not hosts:
            raise ValidationError(_('Network profile must have at least one '
                                    'host.'))

        return hosts

    @staticmethod
    def validate_ssh_port(ssh_port):
        """validate the ssh port."""
        if not ssh_port or ssh_port < 0 or ssh_port > 65536:
            raise ValidationError(_('Network profile must have ssh port in'
                                    ' range [0, 65535]'))

        return ssh_port

    @staticmethod
    def validate_credentials(credentials):
        """Make sure the credentials list is present."""
        if not credentials:
            raise ValidationError(_('Network profile must have at least one'
                                    'set of credentials.'))

        return credentials
