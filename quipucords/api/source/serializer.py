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

import re
import logging
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework.serializers import (ValidationError,
                                        SlugRelatedField, ChoiceField,
                                        PrimaryKeyRelatedField, CharField,
                                        IntegerField)
from api.models import Credential, HostRange, Source
import api.messages as messages
from api.common.serializer import NotEmptySerializer


class HostRangeField(SlugRelatedField):
    """Representation of the host range with in a source."""

    # SlugRelatedField is *almost* what we want for HostRanges, but it
    # doesn't allow creating new HostRanges because it requires them
    # to already exist or else to_internal_value raises a
    # ValidationError, and Serializer.is_valid() will call
    # to_internal_value() before it calls our custom create() method.

    def to_internal_value(self, data):
        """Create internal value."""
        if not isinstance(data, str):
            raise ValidationError(_(messages.NET_HOST_AS_STRING))

        return {'host_range': data}

    def display_value(self, instance):
        """Create display value."""
        return instance.host_range


class CredentialsField(PrimaryKeyRelatedField):
    """Representation of the credentials associated with a source."""

    def to_internal_value(self, data):
        """Create internal value."""
        actual_cred = Credential.objects.filter(id=data).first()
        if actual_cred is None:
            raise ValidationError(_(messages.NET_HC_DO_NOT_EXIST % data))
        return actual_cred

    def to_representation(self, value):
        """Create output representation."""
        return value.id

    def display_value(self, instance):
        """Create display value."""
        display = instance
        if isinstance(instance, Credential):
            display = _(messages.SOURCE_CRED_DISPLAY % instance.name)
        return display


class SourceSerializer(NotEmptySerializer):
    """Serializer for the Source model."""

    name = CharField(required=True, max_length=64)
    source_type = ChoiceField(
        required=False, choices=Source.SOURCE_TYPE_CHOICES)
    port = IntegerField(required=False, min_value=0, allow_null=True)
    hosts = HostRangeField(
        required=False,
        many=True,
        allow_null=True,
        slug_field='host_range',
        queryset=HostRange.objects.all())

    credentials = CredentialsField(
        many=True,
        queryset=Credential.objects.all())

    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = '__all__'

    # Have to implement explicit create() and update() methods to
    # allow creates/updates of nested HostRange field. See
    # http://www.django-rest-framework.org/api-guide/relations/
    # pylint: disable=too-many-branches
    @transaction.atomic
    def create(self, validated_data):
        """Create a source."""
        SourceSerializer.check_for_existing_name(
            name=validated_data.get('name'))

        if 'source_type' not in validated_data:
            raise ValidationError(_(messages.SOURCE_TYPE_REQ))
        source_type = validated_data['source_type']
        credentials = validated_data.pop('credentials')
        hosts_data = validated_data.pop('hosts', None)
        port = None
        if 'port' in validated_data:
            port = validated_data['port']

        if source_type == Source.NETWORK_SOURCE_TYPE:
            if not hosts_data:
                raise ValidationError(_(messages.NET_MIN_HOST))
            if credentials:
                for cred in credentials:
                    SourceSerializer.check_credential_type(source_type, cred)
            if port is None:
                validated_data['port'] = 22
        elif source_type == Source.VCENTER_SOURCE_TYPE:
            if port is None:
                validated_data['port'] = 443
            if not hosts_data:
                raise ValidationError(_(messages.VC_ONE_HOST))
            elif hosts_data and len(hosts_data) != 1:
                raise ValidationError(_(messages.VC_ONE_HOST))
            if credentials and len(credentials) > 1:
                raise ValidationError(_(messages.VC_ONE_CRED))
            elif credentials and len(credentials) == 1:
                SourceSerializer.check_credential_type(source_type,
                                                       credentials[0])

        source = Source.objects.create(**validated_data)

        for host_data in hosts_data:
            HostRange.objects.create(source=source,
                                     **host_data)

        for credential in credentials:
            source.credentials.add(credential)

        return source

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a source."""
        # If we ever add optional fields to Source, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.
        SourceSerializer.check_for_existing_name(
            name=validated_data.get('name'),
            source_id=instance.id)

        if 'source_type' in validated_data:
            raise ValidationError(_(messages.SOURCE_TYPE_INV))
        source_type = instance.source_type
        credentials = validated_data.pop('credentials', None)
        hosts_data = validated_data.pop('hosts', None)

        if source_type == Source.NETWORK_SOURCE_TYPE:
            if credentials:
                for cred in credentials:
                    SourceSerializer.check_credential_type(source_type, cred)
        elif source_type == Source.VCENTER_SOURCE_TYPE:
            if not hosts_data:
                raise ValidationError(_(messages.VC_ONE_HOST))
            elif hosts_data and len(hosts_data) != 1:
                raise ValidationError(_(messages.VC_ONE_HOST))
            if credentials and len(credentials) > 1:
                raise ValidationError(_(messages.VC_ONE_CRED))
            elif credentials and len(credentials) == 1:
                SourceSerializer.check_credential_type(source_type,
                                                       credentials[0])

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
                HostRange.objects.create(source=instance,
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
    def check_for_existing_name(name, source_id=None):
        """Look for existing (different object) with same name.

        :param name: Name of source to look for
        :param source_id: Source to exclude
        """
        if source_id is None:
            # Look for existing with same name (create)
            existing = Source.objects.filter(name=name).first()
        else:
            # Look for existing.  Same name, different id (update)
            existing = Source.objects.filter(
                name=name).exclude(id=source_id).first()
        if existing is not None:
            raise ValidationError(_(messages.SOURCE_NAME_ALREADY_EXISTS %
                                    name))

    @staticmethod
    def check_credential_type(source_type, credential):
        """Look for existing credential with same type as the source.

        :param source_type: The source type
        :param credential: The credential to obtain
        """
        if credential.cred_type != source_type:
            raise ValidationError(_(messages.SOURCE_CRED_WRONG_TYPE))

    @staticmethod
    def validate_name(name):
        """Validate the name of the Source."""
        if not isinstance(name, str) or not name.isprintable():
            raise ValidationError(_(messages.SOURCE_NAME_VALIDATION))

        return name

    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    @staticmethod
    def validate_hosts(hosts):
        """Make sure the hosts list is present."""
        if not hosts:
            raise ValidationError(_(messages.SOURCE_HOSTS_CANNOT_BE_EMPTY))

        # Regex for octet, CIDR bit range, and check
        # to see if it is like an IP/CIDR
        octet_regex = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
        bit_range = r'(3[0-2]|[1-2][0-9]|[0-9])'
        relaxed_ip_pattern = r'[0-9]*\.[0-9]*\.[0-9\[\]:]*\.[0-9\[\]:]*'
        relaxed_cidr_pattern = r'[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\/[0-9]*'
        relaxed_invalid_ip_range = r'[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*-' \
                                   r'[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*'

        # type IP:          192.168.0.1
        # type CIDR:        192.168.0.0/16
        # type RANGE 1:     192.168.0.[1:15]
        # type RANGE 2:     192.168.[2:18].1
        # type RANGE 3:     192.168.[2:18].[4:46]
        ip_regex_list = [
            r'^{0}\.{0}\.{0}\.{0}$'.format(octet_regex),
            r'^{0}\.{0}\.{0}\.{0}\/{1}$'.format(octet_regex, bit_range),
            r'^{0}\.{0}\.{0}\.\[{0}:{0}\]$'.format(octet_regex),
            r'^{0}\.{0}\.\[{0}:{0}\]\.{0}$'.format(octet_regex),
            r'^{0}\.{0}\.\[{0}:{0}\]\.\[{0}:{0}\]$'.format(octet_regex)
        ]

        # type HOST:                abcd
        # type HOST NUMERIC RANGE:  abcd[2:4].foo.com
        # type HOST ALPHA RANGE:    abcd[a:f].foo.com
        host_regex_list = [
            r'[a-zA-Z0-9-\.]+',
            r'[a-zA-Z0-9-\.]*\[[0-9]+:[0-9]+\]*[a-zA-Z0-9-\.]*',
            r'[a-zA-Z0-9-\.]*\[[a-zA-Z]{1}:[a-zA-Z]{1}\][a-zA-Z0-9-\.]*']

        normalized_hosts = []
        host_errors = []
        for host in hosts:
            result = None
            host_range = host['host_range']

            ip_match = re.match(relaxed_ip_pattern, host_range)
            cidr_match = re.match(relaxed_cidr_pattern, host_range)
            invalid_ip_range_match = re.match(relaxed_invalid_ip_range,
                                              host_range)
            is_likely_ip = ip_match and ip_match.end() == len(host_range)
            is_likely_cidr = cidr_match and cidr_match.end() == len(host_range)
            is_likely_invalid_ip_range = (invalid_ip_range_match and
                                          invalid_ip_range_match.end() ==
                                          len(host_range))

            if is_likely_invalid_ip_range:
                err_message = _(messages.NET_INVALID_RANGE_FORMAT %
                                (host_range,))
                result = ValidationError(err_message)

            elif is_likely_ip or is_likely_cidr:
                # This is formatted like an IP or CIDR
                # (e.g. #.#.#.# or #.#.#.#/#)
                for reg in ip_regex_list:
                    match = re.match(reg, host_range)
                    if match and match.end() == len(host_range):
                        result = host
                        break

                if result is None or is_likely_cidr:
                    # Attempt to convert CIDR to ansible range
                    if is_likely_cidr:
                        try:
                            normalized_cidr = SourceSerializer \
                                .cidr_to_ansible(host_range)
                            normalized_cidr_host = {
                                'host_range': normalized_cidr}
                            result = normalized_cidr_host
                        except ValidationError as validate_error:
                            result = validate_error
                    else:
                        err_message = _(messages.NET_INVALID_RANGE_CIDR %
                                        (host_range,))
                        result = ValidationError(err_message)
            else:
                # Possibly a host addr
                for reg in host_regex_list:
                    match = re.match(reg, host_range)
                    if match and match.end() == len(host_range):
                        result = host
                        break
                if result is None:
                    err_message = _(messages.NET_INVALID_HOST % (host_range,))
                    result = ValidationError(err_message)

            if isinstance(result, ValidationError):
                host_errors.append(result)
            elif result is not None:
                normalized_hosts.append(result)
            else:
                # This is an unexpected case. Allow/log for analysis
                normalized_hosts.append(host)
                logging.warning('%s did not match a pattern or produce error',
                                host_range)
        if len(host_errors) is 0:
            return normalized_hosts
        else:
            error_message = [error.detail.pop() for error in host_errors]
            raise ValidationError(error_message)

    # pylint: disable=too-many-locals
    @staticmethod
    def cidr_to_ansible(ip_range):
        """Convert an IP address range from CIDR to Ansible notation.

        :param ip_range: the IP range, as a string
        :returns: the IP range, as an Ansible-formatted string
        :raises NotCIDRException: if ip_range doesn't look similar to CIDR
            notation. If it does look like CIDR but isn't quite right, print
            out error messages and exit.
        """
        # In the case of an input error, we want to distinguish between
        # strings that are "CIDR-like", so the user probably intended to
        # use CIDR and we should give them a CIDR error message, and not
        # at all CIDR-like, in which case we tell the caller to parse it a
        # different way.
        cidr_like = r'[0-9\.]*/[0-9]+'
        if not re.match(cidr_like, ip_range):
            err_msg = _(messages.NET_NO_CIDR_MATCH %
                        (ip_range, str(cidr_like)))
            raise ValidationError(err_msg)

        try:
            base_address, prefix_bits = ip_range.split('/')
        except ValueError:
            err_msg = _(messages.NET_CIDR_INVALID % (ip_range,))
            raise ValidationError(err_msg)

        prefix_bits = int(prefix_bits)

        if prefix_bits < 0 or prefix_bits > 32:
            err_msg = _(messages.NET_CIDR_BIT_MASK %
                        {'ip_range': ip_range, 'prefix_bits': prefix_bits})
            raise ValidationError(err_msg)

        octet_strings = base_address.split('.')
        if len(octet_strings) != 4:
            err_msg = _(messages.NET_FOUR_OCTETS % (ip_range,))
            raise ValidationError(err_msg)

        octets = [None] * 4
        for i in range(4):
            if not octet_strings[i]:
                err_msg = _(messages.NET_EMPTY_OCTET % (ip_range,))
                raise ValidationError(err_msg)

            val = int(octet_strings[i])
            if val < 0 or val > 255:
                # pylint: disable=too-many-locals
                err_msg = _(messages.NET_CIDR_RANGE %
                            {'ip_range': ip_range, 'octet': val})
                raise ValidationError(err_msg)
            octets[i] = val

        ansible_out = [None] * 4
        for i in range(4):
            # "prefix_bits" is the number of high-order bits we want to
            # keep for the whole CIDR range. "mask" is the number of
            # low-order bits we want to mask off. Here prefix_bits is for
            # the whole IP address, but mask_bits is just for this octet.

            if prefix_bits <= i * 8:
                ansible_out[i] = '[0:255]'
            elif prefix_bits >= (i + 1) * 8:
                ansible_out[i] = str(octets[i])
            else:
                # The number of bits of this octet that we want to
                # preserve
                this_octet_bits = prefix_bits - 8 * i
                assert 0 < this_octet_bits < 8
                # mask is this_octet_bits 1's followed by (8 -
                # this_octet_bits) 0's.
                mask = -1 << (8 - this_octet_bits)

                lower_bound = octets[i] & mask
                upper_bound = lower_bound + ~mask
                ansible_out[i] = '[{0}:{1}]'.format(
                    lower_bound, upper_bound)

        return '.'.join(ansible_out)

    @staticmethod
    def validate_port(port):
        """Validate the port."""
        if not port:
            pass
        elif port < 0 or port > 65536:
            raise ValidationError(_(messages.NET_INVALID_PORT))

        return port

    @staticmethod
    def validate_credentials(credentials):
        """Make sure the credentials list is present."""
        if not credentials:
            raise ValidationError(_(messages.NET_MIN_CREDS))

        return credentials
