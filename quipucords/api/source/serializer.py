"""Module for serializing all model object for database storage."""

import ipaddress
import re
from urllib.parse import urlparse

from django.db import transaction
from django.utils.translation import gettext as _
from fqdn import FQDN
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DictField,
    IntegerField,
    JSONField,
    PrimaryKeyRelatedField,
    ValidationError,
)

from api import API_VERSION, messages
from api.common.serializer import (
    ModelSerializer,
    NotEmptySerializer,
    ValidStringChoiceField,
)
from api.common.util import check_for_existing_name
from api.models import Credential, Source
from constants import DataSources
from utils import get_from_object_or_dict

MAX_PORT = 65536
MIN_PORT = 0


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


class SourceSerializerBase(ModelSerializer):
    """Serializer for the Source model."""

    def __init__(self, *args, **kwargs):
        if self is SourceSerializerBase:
            raise Exception("SourceSerializerBase must be subclassed.")
        super().__init__(*args, **kwargs)

    name = CharField(required=True, max_length=64)
    source_type = ValidStringChoiceField(
        required=False,
        choices=DataSources.choices,
    )
    port = IntegerField(required=False, min_value=0, allow_null=True)
    hosts = JSONField(required=True)
    exclude_hosts = JSONField(required=False)

    credentials = CredentialsField(many=True, queryset=Credential.objects.all())

    HTTP_SOURCE_TYPES = (
        DataSources.RHACS,
        DataSources.ANSIBLE,
        DataSources.OPENSHIFT,
        DataSources.SATELLITE,
        DataSources.VCENTER,
    )

    SSH_SOURCE_TYPES = (DataSources.NETWORK,)
    SSL_OPTIONS = ["ssl_cert_verify", "ssl_protocol", "disable_ssl", "use_paramiko"]

    class Meta:
        """Metadata for the serializer."""

        model = Source
        exclude = (
            "created_at",
            "updated_at",
        )  # TODO Include these datetime fields in a future API version.

    @classmethod
    def validate_opts(cls, options, source_type, *, apply_defaults=True):
        """Raise an error if options are invalid for the source type.

        :param options: dictionary of source options
        :param source_type: string denoting source type
        :param apply_defaults: set defaults (e.g., ssl_cert_verify) in V1 create only
        """
        # TODO: Remove `apply_defaults` logic once V1 is fully deprecated.
        # V1 sets defaults here (e.g., ssl_cert_verify=True).
        # V2 handles this in validate_http_source() to follow DRF style.
        valid_ssh_options = ["use_paramiko"]
        valid_http_options = ["ssl_cert_verify", "ssl_protocol", "disable_ssl"]

        if source_type in cls.HTTP_SOURCE_TYPES:
            if apply_defaults:
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

    def update_options(self, options, instance):
        """Update the incoming options overlapping the instance options.

        :param options: the passed in options
        :param instance: the existing instance
        """
        for ssl_option in self.SSL_OPTIONS:
            value = options.pop(ssl_option, None)
            if value is not None:
                setattr(instance, ssl_option, value)

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
        if hosts_list and ("[" in hosts_list[0] or "/" in hosts_list[0]):
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

    def create_base(self, validated_data):
        """Create a source."""
        # Note: Superclass create should be wrapped as an atomic transaction.
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

        source = Source.objects.create(**validated_data)
        source_options = source.options

        if source_options:
            SourceSerializer.validate_opts(source_options, source_type)
        elif source_type in self.HTTP_SOURCE_TYPES:
            source.ssl_cert_verify = True

        source.hosts = hosts_list
        if exclude_hosts_list:
            source.exclude_hosts = exclude_hosts_list

        for credential in credentials:
            source.credentials.add(credential)

        source.save()
        return source

    @staticmethod
    def update_base(instance, validated_data):
        """Update a source."""
        # Note: Superclass update should be wrapped as an atomic transaction.
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
        credentials = validated_data.pop("credentials", None)
        hosts_list = validated_data.pop("hosts", None)
        exclude_hosts_list = validated_data.pop("exclude_hosts", None)

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

        instance.save()
        return instance

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
    def validate_addresses(addresses: list) -> list:
        """
        Validate a list of IP addresses, CIDRs, hostnames, and Ansible ranges.

        Returns list of normalized addresses if valid, otherwise raises ValidationError.
        """
        # Initial List Processing
        if not isinstance(addresses, list):
            raise ValidationError(_(messages.SOURCE_HOST_MUST_BE_JSON_ARRAY))

        addresses = [address for address in addresses if address]

        if not addresses:
            raise ValidationError(_(messages.SOURCE_HOSTS_CANNOT_BE_EMPTY))

        for address in addresses:
            if not isinstance(address, str):
                raise ValidationError(_(messages.SOURCE_HOST_MUST_BE_JSON_ARRAY))

        normalized_addresses = []
        address_errors = []

        for address in addresses:
            try:
                normalized_addresses.extend(
                    SourceSerializer.classify_and_validate_address(address)
                )
            except ValidationError as error:
                address_errors.append(error)

        if address_errors:
            error_message = [msg for error in address_errors for msg in error.detail]
            raise ValidationError(error_message)

        return normalized_addresses

    @staticmethod
    def classify_and_validate_address(address: str) -> list:
        """
        Classify and validate an address as an IP, CIDR, hostname, or Ansible range.

        Returns a list of valid addresses or raises a ValidationError.
        """
        if SourceSerializer.is_valid_ip(address):
            return [address]

        if SourceSerializer.is_valid_cidr(address):
            return [address]

        if SourceSerializer.is_valid_hostname(address):
            return [address]

        if SourceSerializer.is_valid_ansible_range(address):
            return [address]

        raise ValidationError(_(messages.NET_INVALID_HOST % (address,)))

    @staticmethod
    def is_valid_ip(address: str) -> bool:
        """Check if the input is a valid IPv4 or IPv6 address."""
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_cidr(address: str) -> bool:
        """Check if the input is a valid CIDR block."""
        try:
            ipaddress.ip_network(address, strict=False)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_hostname(address: str) -> bool:
        """Check if the input is a valid FQDN hostname."""
        try:
            return FQDN(address).is_valid
        except ValueError:
            return False

    @staticmethod
    def is_valid_ansible_range(address: str) -> bool:
        """Check if the input matches Ansible range syntax [x:y]."""
        if not isinstance(address, str):
            return False

        # Ensure it follows Ansible-style range [x:y]
        if not re.search(r"\[\d+:\d+\]", address):
            return False

        if "/" in address:
            return False

        return True

    @staticmethod
    def validate_hosts(hosts):
        """Validate hosts list."""
        return SourceSerializer.validate_addresses(hosts)

    @staticmethod
    def validate_exclude_hosts(exclude_hosts):
        """Validate exclude_hosts list."""
        return SourceSerializer.validate_addresses(exclude_hosts)

    @staticmethod
    def validate_port(port):
        """Validate the port is either None or an integer within the allowed range."""
        if port is None:
            return port

        if not isinstance(port, int):
            raise ValidationError(_(messages.INVALID_PORT))

        if port < MIN_PORT or port > MAX_PORT:
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
        """Validate the attributes for HTTP-based sources."""
        credentials = attrs.get("credentials")
        hosts_list = attrs.get("hosts")
        exclude_hosts_list = attrs.get("exclude_hosts")

        if source_type == DataSources.OPENSHIFT:
            default_port = 6443
        else:
            default_port = 443
        self._set_default_port(attrs, default_port)

        # Only apply ssl_cert_verify default if:
        # - we're creating
        # - and the field was not passed explicitly
        if not self.instance and "ssl_cert_verify" not in self.initial_data:
            attrs["ssl_cert_verify"] = True

        self._validate_number_hosts_and_credentials(
            hosts_list,
            source_type,
            credentials,
            exclude_hosts_list,
        )
        return attrs


class SourceSerializerV1(NotEmptySerializer, SourceSerializerBase):
    """V1 Serializer for the Source model."""

    options = DictField(required=False, default={})

    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = (
            "id",
            "name",
            "source_type",
            "port",
            "hosts",
            "exclude_hosts",
            "options",
            "credentials",
            "most_recent_connect_scan",
        )

    @transaction.atomic
    def create(self, validated_data):
        """Create a V1 source."""
        options = validated_data.pop("options", None)
        instance = super().create_base(validated_data)
        if options:
            source_type = instance.source_type
            self.validate_opts(options, source_type)
            instance.ssl_protocol = options.get("ssl_protocol")
            instance.ssl_cert_verify = options.get("ssl_cert_verify")
            instance.disable_ssl = options.get("disable_ssl")
            instance.use_paramiko = options.get("use_paramiko")
            instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a V1 source."""
        options = validated_data.pop("options", None)
        instance = super().update_base(instance, validated_data)
        # If SSL options were specified via the options property,
        # let's validate those and overwrite the instance's properties.
        if options:
            source_type = instance.source_type
            self.validate_opts(options, source_type)
            self.update_options(options, instance)
            instance.save()
        return instance


class SourceSerializerV2(SourceSerializerBase):
    """V2 Serializer for the Source model."""

    ssl_protocol = ValidStringChoiceField(
        required=False, choices=Source.SSL_PROTOCOL_CHOICES
    )
    ssl_cert_verify = BooleanField(allow_null=True, required=False)
    disable_ssl = BooleanField(allow_null=True, required=False)
    use_paramiko = BooleanField(allow_null=True, required=False)
    proxy_url = CharField(required=False, allow_null=True, max_length=255)

    # Dropping options in preference for showing the direct ssl option attributes.
    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = (
            "id",
            "name",
            "source_type",
            "port",
            "hosts",
            "exclude_hosts",
            "ssl_protocol",
            "ssl_cert_verify",
            "disable_ssl",
            "use_paramiko",
            "proxy_url",
            "credentials",
            "most_recent_connect_scan",
        )

    def validate_proxy_url(self, value):
        """Validate that proxy URL is in the 'http(s)://host:port' format."""
        if not value:
            return value

        self.is_valid_proxy_url_format(value)
        return value

    @staticmethod
    def is_valid_proxy_url_format(proxy_url):
        """Check that the proxy URL is in 'http(s)://host:port' format."""
        parsed = urlparse(proxy_url)

        if parsed.scheme not in ("http", "https"):
            raise ValidationError(_(messages.SOURCE_INVALID_SCHEMA_PROXY_URL))
        if not parsed.hostname:
            raise ValidationError(_(messages.SOURCE_INVALID_HOST_PROXY_URL))
        if not re.match(r"^[a-zA-Z0-9.-]+$", parsed.hostname):
            raise ValidationError(_(messages.SOURCE_INVALID_HOST_PROXY_URL))
        if not parsed.port or not (MIN_PORT < parsed.port < MAX_PORT):
            raise ValidationError(_(messages.SOURCE_INVALID_PORT_PROXY_URL))

    @transaction.atomic
    def create(self, validated_data):
        """Create a V2 source."""
        return super().create_base(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a V2 source."""
        ssl_options = {}
        for ssl_option in self.SSL_OPTIONS:
            value = validated_data.pop(ssl_option, None)
            if value is not None:
                ssl_options[ssl_option] = value
        instance = super().update_base(instance, validated_data)
        if ssl_options:
            source_type = instance.source_type
            self.validate_opts(ssl_options, source_type, apply_defaults=False)
            self.update_options(ssl_options, instance)
            instance.save()
        return instance


# Let's define the SourceSerializer based on the API_VERSION
match API_VERSION:
    case 2:
        SourceSerializer = SourceSerializerV2
    case _:
        SourceSerializer = SourceSerializerV1
