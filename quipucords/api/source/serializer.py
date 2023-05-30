"""Module for serializing all model object for database storage."""

import logging
import re

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    JSONField,
    PrimaryKeyRelatedField,
    ValidationError,
)

from api import messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.common.util import check_for_existing_name
from api.models import Credential, Source, SourceOptions
from constants import DataSources
from utils import get_from_object_or_dict


class CredentialsField(PrimaryKeyRelatedField):
    """Representation of the credentials associated with a source."""

    def to_internal_value(self, data):
        """Create internal value."""
        if not isinstance(data, int):
            raise ValidationError(_(messages.SOURCE_CRED_IDS_INV))
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


class SourceOptionsSerializer(NotEmptySerializer):
    """Serializer for the SourceOptions model."""

    ssl_protocol = ValidStringChoiceField(
        required=False, choices=SourceOptions.SSL_PROTOCOL_CHOICES
    )
    ssl_cert_verify = BooleanField(allow_null=True, required=False)
    disable_ssl = BooleanField(allow_null=True, required=False)
    use_paramiko = BooleanField(allow_null=True, required=False)

    class Meta:
        """Metadata for serializer."""

        model = SourceOptions
        fields = ["ssl_protocol", "ssl_cert_verify", "disable_ssl", "use_paramiko"]


class SourceSerializer(NotEmptySerializer):
    """Serializer for the Source model."""

    name = CharField(required=True, max_length=64)
    source_type = ValidStringChoiceField(
        required=False,
        choices=DataSources.choices,
    )
    port = IntegerField(required=False, min_value=0, allow_null=True)
    hosts = JSONField(required=True)
    exclude_hosts = JSONField(required=False)
    options = SourceOptionsSerializer(required=False, many=False)
    credentials = CredentialsField(many=True, queryset=Credential.objects.all())

    HTTP_SOURCE_TYPES = (
        DataSources.ANSIBLE,
        DataSources.OPENSHIFT,
        DataSources.SATELLITE,
        DataSources.VCENTER,
    )

    SSH_SOURCE_TYPES = (DataSources.NETWORK,)

    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = "__all__"

    @classmethod
    def validate_opts(cls, options, source_type):
        """Raise an error if options are invalid for the source type.

        :param options: dictionary of source options
        :param source_type: string denoting source type
        """
        valid_ssh_options = ["use_paramiko"]
        valid_http_options = ["ssl_cert_verify", "ssl_protocol", "disable_ssl"]

        if source_type in cls.HTTP_SOURCE_TYPES:
            options.setdefault("ssl_cert_verify", True)
            cls._check_for_disallowed_fields(
                options,
                messages.INVALID_OPTIONS,
                valid_http_options,
                source_type,
            )
        elif source_type in cls.SSH_SOURCE_TYPES:
            cls._check_for_disallowed_fields(
                options,
                messages.NET_SSL_OPTIONS_NOT_ALLOWED,
                valid_ssh_options,
                source_type,
            )
        else:
            raise NotImplementedError

    @classmethod
    def _check_for_disallowed_fields(cls, options, message, valid_fields, source_type):
        """Verify if disallowed fields are present."""
        invalid_options = [opt for opt in options if opt not in valid_fields]
        if invalid_options:
            error = {
                "options": [
                    _(message)
                    % {
                        "source_type": source_type,
                        "options": ", ".join(invalid_options),
                    }
                ]
            }
            raise ValidationError(error)

    def _validate_number_hosts_and_credentials(
        self, hosts_list, source_type, credentials, exclude_hosts_list
    ):
        """Verify if each source received appropriate number of hosts and creds."""
        if hosts_list and len(hosts_list) != 1:
            error = {"hosts": [_(messages.SOURCE_ONE_HOST)]}
            raise ValidationError(error)
        if hosts_list and "[" in hosts_list[0]:
            error = {"hosts": [_(messages.SOURCE_ONE_HOST)]}
            raise ValidationError(error)
        if exclude_hosts_list is not None:
            error = {"exclude_hosts": [_(messages.SOURCE_EXCLUDE_HOSTS_INCLUDED)]}
            raise ValidationError(error)
        if credentials and len(credentials) > 1:
            error = {"credentials": [_(messages.SOURCE_ONE_CRED)]}
            raise ValidationError(error)
        if credentials and len(credentials) == 1:
            SourceSerializer.check_credential_type(source_type, credentials[0])

    def _options_with_ssl_cert_verify_true(self, source):
        """Add options to source with ssl_cert_verify flag set to true."""
        options = SourceOptions()
        options.ssl_cert_verify = True
        options.save()
        source.options = options

    def validate(self, attrs):
        """Validate if fields received are appropriate for each credential."""
        source_type = get_from_object_or_dict(self.instance, attrs, "source_type")
        if source_type in self.SSH_SOURCE_TYPES:
            validated_data = self.validate_network_source(attrs, source_type)
        elif source_type in self.HTTP_SOURCE_TYPES:
            validated_data = self.validate_http_source(attrs, source_type)
        else:
            raise ValidationError({"source_type": messages.UNKNOWN_SOURCE_TYPE})
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        """Create a source."""
        name = validated_data.get("name")
        check_for_existing_name(
            Source.objects, name, _(messages.SOURCE_NAME_ALREADY_EXISTS % name)
        )

        if "source_type" not in validated_data:
            error = {"source_type": [_(messages.SOURCE_TYPE_REQ)]}
            raise ValidationError(error)
        source_type = validated_data.get("source_type")
        credentials = validated_data.pop("credentials")
        hosts_list = validated_data.pop("hosts", None)
        exclude_hosts_list = validated_data.pop("exclude_hosts", None)
        options = validated_data.pop("options", None)

        source = Source.objects.create(**validated_data)

        if options:
            SourceSerializer.validate_opts(options, source_type)
            options = SourceOptions.objects.create(**options)
            options.save()
            source.options = options
        elif not options and source_type in self.HTTP_SOURCE_TYPES:
            self._options_with_ssl_cert_verify_true(source)

        source.hosts = hosts_list
        if exclude_hosts_list:
            source.exclude_hosts = exclude_hosts_list

        for credential in credentials:
            source.credentials.add(credential)

        source.save()
        return source

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a source."""
        # If we ever add optional fields to Source, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.
        name = validated_data.get("name")
        check_for_existing_name(
            Source.objects,
            name,
            _(messages.SOURCE_NAME_ALREADY_EXISTS % name),
            search_id=instance.id,
        )

        if "source_type" in validated_data:
            error = {"source_type": [_(messages.SOURCE_TYPE_INV)]}
            raise ValidationError(error)
        source_type = instance.source_type
        credentials = validated_data.pop("credentials", None)
        hosts_list = validated_data.pop("hosts", None)
        exclude_hosts_list = validated_data.pop("exclude_hosts", None)
        options = validated_data.pop("options", None)

        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()

        # If hosts_list was not supplied and this is a full update,
        # then we should already have raised a ValidationError before
        # this point, so it's safe to use hosts_list as an indicator
        # of whether to replace the hosts.
        if hosts_list:
            instance.hosts = hosts_list

        if exclude_hosts_list:
            instance.exclude_hosts = exclude_hosts_list

        # credentials is safe to use as a flag for the same reason as
        # hosts_data above.
        if credentials:
            instance.credentials.set(credentials)

        if options:
            SourceSerializer.validate_opts(options, source_type)
            if instance.options is None:
                options = SourceOptions.objects.create(**options)
                options.save()
                instance.options = options
            else:
                self.update_options(options, instance.options)

        instance.save()
        return instance

    @staticmethod
    def update_options(options, instance_options):
        """Update the incoming options overlapping the existing options.

        :param options: the passed in options
        :param instance_options: the existing options
        """
        ssl_protocol = options.pop("ssl_protocol", None)
        ssl_cert_verify = options.pop("ssl_cert_verify", None)
        disable_ssl = options.pop("disable_ssl", None)
        use_paramiko = options.pop("use_paramiko", None)
        if ssl_protocol is not None:
            instance_options.ssl_protocol = ssl_protocol
        if ssl_cert_verify is not None:
            instance_options.ssl_cert_verify = ssl_cert_verify
        if disable_ssl is not None:
            instance_options.disable_ssl = disable_ssl
        if use_paramiko is not None:
            instance_options.use_paramiko = use_paramiko
        instance_options.save()

    @staticmethod
    def check_credential_type(source_type, credential):
        """Look for existing credential with same type as the source.

        :param source_type: The source type
        :param credential: The credential to obtain
        """
        if credential.cred_type != source_type:
            error = {"source_type": [_(messages.SOURCE_CRED_WRONG_TYPE)]}
            raise ValidationError(error)

    @staticmethod
    def validate_name(name):
        """Validate the name of the Source."""
        if not isinstance(name, str) or not name.isprintable():
            raise ValidationError(_(messages.SOURCE_NAME_VALIDATION))

        return name

    @staticmethod
    def validate_ipaddr_list(hosts):  # noqa: PLR0912, PLR0915, C901
        """Make sure the hosts list is present and has valid IP addresses."""
        ipaddr_list = hosts
        if isinstance(ipaddr_list, list):
            ipaddr_list = [item for item in ipaddr_list if item]

        if not isinstance(ipaddr_list, list):
            raise ValidationError(_(messages.SOURCE_HOST_MUST_BE_JSON_ARRAY))

        if not ipaddr_list:
            raise ValidationError(_(messages.SOURCE_HOSTS_CANNOT_BE_EMPTY))

        for host_value in ipaddr_list:
            if not isinstance(host_value, str):
                raise ValidationError(_(messages.SOURCE_HOST_MUST_BE_JSON_ARRAY))

        # Regex for octet, CIDR bit range, and check
        # to see if it is like an IP/CIDR
        octet_regex = r"(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])"
        bit_range = r"(3[0-2]|[1-2][0-9]|[0-9])"
        relaxed_ip_pattern = r"[0-9]*\.[0-9]*\.[0-9\[\]:]*\.[0-9\[\]:]*"
        relaxed_cidr_pattern = r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\/[0-9]*"
        greedy_subset = r"[0-9]*"
        range_subset = r"[0-9]*-[0-9]*"
        relaxed_invalid_ip_range = [
            r"{0}\.{0}\.{0}\.{0}-{0}\.{0}\.{0}\.{0}".format(greedy_subset),
            r"{0}\.{0}\.{0}\.{1}".format(greedy_subset, range_subset),
            r"{0}\.{0}\.{1}\.{0}".format(greedy_subset, range_subset),
            r"{0}\.{1}\.{0}\.{0}".format(greedy_subset, range_subset),
            r"{1}\.{0}\.{0}\.{0}".format(greedy_subset, range_subset),
            r"{1}\.{1}\.{0}\.{0}".format(greedy_subset, range_subset),
            r"{1}\.{0}\.{1}\.{0}".format(greedy_subset, range_subset),
            r"{1}\.{0}\.{0}\.{1}".format(greedy_subset, range_subset),
            r"{1}\.{1}\.{0}\.{1}".format(greedy_subset, range_subset),
            r"{1}\.{0}\.{1}\.{1}".format(greedy_subset, range_subset),
            r"{0}\.{0}\.{0}\.{0}".format(range_subset),
            r"{0}\.{1}\.{0}\.{1}".format(greedy_subset, range_subset),
            r"{0}\.{1}\.{1}\.{0}".format(greedy_subset, range_subset),
        ]

        # type IP:          192.168.0.1
        # type CIDR:        192.168.0.0/16
        # type RANGE 1:     192.168.0.[1:15]
        # type RANGE 2:     192.168.[2:18].1
        # type RANGE 3:     192.168.[2:18].[4:46]
        ip_regex_list = [
            r"^{0}\.{0}\.{0}\.{0}$".format(octet_regex),
            r"^{0}\.{0}\.{0}\.{0}\/{1}$".format(octet_regex, bit_range),
            r"^{0}\.{0}\.{0}\.\[{0}:{0}\]$".format(octet_regex),
            r"^{0}\.{0}\.\[{0}:{0}\]\.{0}$".format(octet_regex),
            r"^{0}\.{0}\.\[{0}:{0}\]\.\[{0}:{0}\]$".format(octet_regex),
        ]

        # type HOST:                abcd
        # type HOST NUMERIC RANGE:  abcd[2:4].foo.com
        # type HOST ALPHA RANGE:    abcd[a:f].foo.com
        host_regex_list = [
            r"[a-zA-Z0-9-_\.]+",
            r"[a-zA-Z0-9-_\.]*\[[0-9]+:[0-9]+\]*[a-zA-Z0-9-_\.]*",
            r"[a-zA-Z0-9-_\.]*\[[a-zA-Z]{1}:[a-zA-Z]{1}\][a-zA-Z0-9-_\.]*",
        ]

        normalized_hosts = []
        host_errors = []
        for host_range in ipaddr_list:
            result = None
            ip_match = re.match(relaxed_ip_pattern, host_range)
            cidr_match = re.match(relaxed_cidr_pattern, host_range)
            invalid_ip_range_match = [
                re.match(invalid_ip_range, host_range)
                for invalid_ip_range in relaxed_invalid_ip_range
            ]
            is_likely_ip = ip_match and ip_match.end() == len(host_range)
            is_likely_cidr = cidr_match and cidr_match.end() == len(host_range)
            is_likely_invalid_ip_range = any(invalid_ip_range_match)

            if is_likely_invalid_ip_range:
                err_message = _(messages.NET_INVALID_RANGE_FORMAT % (host_range,))
                result = ValidationError(err_message)

            elif is_likely_ip or is_likely_cidr:
                # This is formatted like an IP or CIDR
                # (e.g. #.#.#.# or #.#.#.#/#)
                for reg in ip_regex_list:
                    match = re.match(reg, host_range)
                    if match and match.end() == len(host_range):
                        result = host_range
                        break

                if result is None or is_likely_cidr:
                    # Attempt to convert CIDR to ansible range
                    if is_likely_cidr:
                        try:
                            normalized_cidr = SourceSerializer.cidr_to_ansible(
                                host_range
                            )
                            result = normalized_cidr
                        except ValidationError as validate_error:
                            result = validate_error
                    else:
                        err_message = _(messages.NET_INVALID_RANGE_CIDR % (host_range,))
                        result = ValidationError(err_message)
            else:
                # Possibly a host_range addr
                for reg in host_regex_list:
                    match = re.match(reg, host_range)
                    if match and match.end() == len(host_range):
                        result = host_range
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
                normalized_hosts.append(host_range)
                logging.warning(
                    "%s did not match a pattern or produce error", host_range
                )
        if not host_errors:
            return normalized_hosts
        error_message = [error.detail.pop() for error in host_errors]
        raise ValidationError(error_message)

    @staticmethod
    def validate_hosts(hosts):
        """Validate hosts list."""
        return SourceSerializer.validate_ipaddr_list(hosts)

    @staticmethod
    def validate_exclude_hosts(exclude_hosts):
        """Validate exclude_hosts list."""
        return SourceSerializer.validate_ipaddr_list(exclude_hosts)

    @staticmethod
    def cidr_to_ansible(ip_range):  # noqa: C901
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
        cidr_like = r"[0-9\.]*/[0-9]+"
        if not re.match(cidr_like, ip_range):
            err_msg = _(messages.NET_NO_CIDR_MATCH % (ip_range, str(cidr_like)))
            raise ValidationError(err_msg)

        try:
            base_address, prefix_bits = ip_range.split("/")
        except ValueError as err:
            err_msg = _(messages.NET_CIDR_INVALID % (ip_range,))
            raise ValidationError(err_msg) from err

        prefix_bits = int(prefix_bits)

        if prefix_bits < 0 or prefix_bits > 32:  # noqa: PLR2004
            err_msg = _(
                messages.NET_CIDR_BIT_MASK
                % {"ip_range": ip_range, "prefix_bits": prefix_bits}
            )
            raise ValidationError(err_msg)

        octet_strings = base_address.split(".")
        if len(octet_strings) != 4:  # noqa: PLR2004
            err_msg = _(messages.NET_FOUR_OCTETS % (ip_range,))
            raise ValidationError(err_msg)

        octets = [None] * 4
        for i in range(4):
            if not octet_strings[i]:
                err_msg = _(messages.NET_EMPTY_OCTET % (ip_range,))
                raise ValidationError(err_msg)

            val = int(octet_strings[i])
            if val < 0 or val > 255:  # noqa: PLR2004

                err_msg = _(
                    messages.NET_CIDR_RANGE % {"ip_range": ip_range, "octet": val}
                )
                raise ValidationError(err_msg)
            octets[i] = val

        ansible_out = [None] * 4
        for i in range(4):
            # "prefix_bits" is the number of high-order bits we want to
            # keep for the whole CIDR range. "mask" is the number of
            # low-order bits we want to mask off. Here prefix_bits is for
            # the whole IP address, but mask_bits is just for this octet.

            if prefix_bits <= i * 8:
                ansible_out[i] = "[0:255]"
            elif prefix_bits >= (i + 1) * 8:
                ansible_out[i] = str(octets[i])
            else:
                # The number of bits of this octet that we want to
                # preserve
                this_octet_bits = prefix_bits - 8 * i
                assert 0 < this_octet_bits < 8  # noqa: PLR2004
                # mask is this_octet_bits 1's followed by (8 -
                # this_octet_bits) 0's.
                mask = -1 << (8 - this_octet_bits)

                lower_bound = octets[i] & mask
                upper_bound = lower_bound + ~mask
                ansible_out[i] = f"[{lower_bound}:{upper_bound}]"

        return ".".join(ansible_out)

    @staticmethod
    def validate_port(port):
        """Validate the port."""
        if not port:
            pass
        elif port < 0 or port > 65536:  # noqa: PLR2004
            raise ValidationError(_(messages.NET_INVALID_PORT))

        return port

    @staticmethod
    def validate_credentials(credentials):
        """Make sure the credentials list is present."""
        if not credentials:
            raise ValidationError(_(messages.SOURCE_MIN_CREDS))

        return credentials

    def _set_default_port(self, attrs, port_number):
        port = get_from_object_or_dict(self.instance, attrs, "port")
        if not port:
            attrs["port"] = port_number

    def validate_network_source(self, attrs, source_type):
        """Validate the attributes for network source."""
        credentials = attrs.get("credentials")
        self._set_default_port(attrs, 22)
        if credentials:
            for cred in credentials:
                SourceSerializer.check_credential_type(source_type, cred)
        return attrs

    def validate_http_source(self, attrs, source_type):
        """Validate the attributes for vcenter source."""
        credentials = attrs.get("credentials")
        hosts_list = attrs.get("hosts")
        exclude_hosts_list = attrs.get("exclude_hosts")
        if source_type == DataSources.OPENSHIFT:
            default_port = 6443
        else:
            default_port = 443
        self._set_default_port(attrs, default_port)
        self._validate_number_hosts_and_credentials(
            hosts_list,
            source_type,
            credentials,
            exclude_hosts_list,
        )
        return attrs
