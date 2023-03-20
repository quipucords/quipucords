"""Module for serializing all model object for database storage."""

import os
from collections import defaultdict

from django.utils.translation import gettext as _
from rest_framework.serializers import CharField, ValidationError, empty

from api import messages
from api.common.serializer import NotEmptySerializer
from api.common.util import check_for_existing_name
from api.models import Credential
from constants import DataSources


def expand_filepath(filepath):
    """Expand the ssh_keyfile filepath if necessary."""
    if filepath is not None:
        expanded = os.path.abspath(
            os.path.normpath(os.path.expanduser(os.path.expandvars(filepath)))
        )
        return expanded
    return filepath


ENCRYPTED_FIELD_KWARGS = {"style": {"input_type": "password"}}
SERIALIZER_PER_DATASOURCE = {}


class CredentialSerializer:
    """Proxy for Credential Serializers.

    This class reads instance and data args/kwargs to figure out the appropriate
    serializer class to return.
    """

    def __new__(cls, instance=None, data=empty, **kwargs):
        """Initialize the adequate serializer."""
        klass = cls._get_serializer_class(instance, data)
        return klass(instance=instance, data=data, **kwargs)

    @classmethod
    def _get_serializer_class(cls, instance: Credential, data: dict):
        if not instance and data == empty:
            return BaseCredentialSerializer
        if isinstance(instance, list):
            return BaseCredentialSerializer
        cred_type = cls._get_cred_type(instance, data)
        if not cred_type:
            return BaseCredentialSerializer
        try:
            return SERIALIZER_PER_DATASOURCE[cred_type]
        except KeyError:
            # this KeyError won't add anything to the tb
            # pylint: disable=raise-missing-from
            raise NotImplementedError(f"No serializer implemented for {cred_type=}")

    @classmethod
    def _get_cred_type(cls, instance, data):
        if instance:
            return instance.cred_type
        if isinstance(data, dict) and data.get("cred_type") in DataSources.values:
            return data["cred_type"]
        return None


class BaseCredentialSerializer(NotEmptySerializer):
    """Base Serializer for the Credential model.

    Specialized Credential serializers should be created inheriting from this one
    and MUST have a 'qpc_data_sources' set in its 'Meta' configuration class.

    Here's one example:

    class NewCredentialSerializer(BaseCredentialSerializer):
        class Meta:
            model = Credential
            fields = ["id", "name", "cred_type", "new_field"]
            extra_kwargs = {
                "new_field": {"required": True, **ENCRYPTED_FIELD_KWARGS},
            }
            qpc_data_sources = [DataSources.NEW_SOURCE]
    """

    name = CharField(required=True, max_length=64)

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = "__all__"
        extra_kwargs = {
            "password": ENCRYPTED_FIELD_KWARGS,
            "auth_token": ENCRYPTED_FIELD_KWARGS,
            "ssh_passphrase": ENCRYPTED_FIELD_KWARGS,
            "become_password": ENCRYPTED_FIELD_KWARGS,
        }

    def __init__(self, instance=None, data=empty, **kwargs):
        """Customize class initialization."""
        if instance and isinstance(data, dict):
            # assume cred_type == instance.cred_type if not provided
            # this is only required to avoid breaking current functionality
            # that was treating 'cred_type' as optional for updates and required for
            # credential creation
            data.setdefault("cred_type", instance.cred_type)
        super().__init__(instance=instance, data=data, **kwargs)

    def __init_subclass__(cls, **kwargs):
        """Overload subclass creation method."""
        super().__init_subclass__(**kwargs)
        if not getattr(cls.Meta, "qpc_data_sources", None):
            raise NotImplementedError(
                "subclasses of CredentialSerializer MUST have a 'Meta' class "
                "with 'qpc_data_sources' set as a list of DataSources."
            )

        # pylint doesn't know cls in __init_subclass__ refer to it's subclasses...
        # pylint: disable=no-member
        for data_source in cls.Meta.qpc_data_sources:
            # pylint: enable=no-member
            if data_source in SERIALIZER_PER_DATASOURCE:
                raise RuntimeError(
                    f"Data source {data_source} already has a serializer set "
                    f"({SERIALIZER_PER_DATASOURCE[data_source].__name__})."
                )
            SERIALIZER_PER_DATASOURCE[data_source] = cls

    def validate_cred_type(self, cred_type):
        """Validate cred_type field."""
        if self.instance and cred_type != self.instance.cred_type:
            raise ValidationError((messages.CRED_TYPE_NOT_ALLOWED_UPDATE))
        return cred_type

    def validate(self, attrs):
        """Validate if fields received are appropriate for each credential."""
        errors = {}
        if hasattr(self, "initial_data"):
            unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
            for key in unknown_keys:
                errors[key] = (
                    messages.FIELD_NOT_ALLOWED_FOR_DATA_SOURCE % attrs["cred_type"]
                )
        if errors:
            raise ValidationError(errors)
        return attrs

    def create(self, validated_data):
        """Create host credential."""
        name = validated_data.get("name")
        check_for_existing_name(
            Credential.objects, name, _(messages.HC_NAME_ALREADY_EXISTS % name)
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a host credential."""
        name = validated_data.get("name")
        check_for_existing_name(
            Credential.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name),
            search_id=instance.id,
        )
        return super().update(instance, validated_data)


class AuthTokenSerializer(BaseCredentialSerializer):
    """Serializer for credentials that require only auth_token."""

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = ["id", "name", "cred_type", "auth_token"]
        extra_kwargs = {
            "auth_token": {"required": True, **ENCRYPTED_FIELD_KWARGS},
        }
        qpc_data_sources = [DataSources.OPENSHIFT]


class UsernamePasswordSerializer(BaseCredentialSerializer):
    """Serializer for credentials that require username and password."""

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = [
            "cred_type",
            "id",
            "name",
            "password",
            "username",
        ]
        extra_kwargs = {
            "password": {"required": True, **ENCRYPTED_FIELD_KWARGS},
            "username": {"required": True},
        }
        qpc_data_sources = [DataSources.SATELLITE, DataSources.VCENTER]


class NetworkCredentialSerializer(BaseCredentialSerializer):
    """Serializer class for network scan credentials."""

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = [
            "id",
            "name",
            "become_method",
            "become_password",
            "become_user",
            "cred_type",
            "password",
            "ssh_keyfile",
            "ssh_passphrase",
            "username",
        ]
        extra_kwargs = {
            "become_method": {"default": Credential.BECOME_SUDO},
            "become_password": ENCRYPTED_FIELD_KWARGS,
            "become_user": {"default": Credential.BECOME_USER_DEFAULT},
            "password": ENCRYPTED_FIELD_KWARGS,
            "ssh_passphrase": ENCRYPTED_FIELD_KWARGS,
            "username": {"required": True},
        }
        qpc_data_sources = [DataSources.NETWORK]

    def validate_ssh_keyfile(self, ssh_keyfile):
        """Validate ssh_keyfile field."""
        keyfile = expand_filepath(ssh_keyfile)
        if not os.path.isfile(keyfile):
            raise ValidationError(_(messages.HC_KEY_INVALID % (ssh_keyfile)))
        return keyfile

    def validate(self, attrs):
        """Validate fields that need to be evaluated together."""
        try:
            data = super().validate(attrs)
            errors = defaultdict(list)
        except ValidationError as exc:
            data = attrs
            errors = exc.get_full_details()
        password = data.get("password")
        ssh_keyfile = data.get("ssh_keyfile")
        ssh_passphrase = data.get("ssh_passphrase")

        if password and ssh_keyfile:
            errors["non_field_errors"].append(_(messages.HC_NOT_BOTH))
        if not self.partial and not (password or ssh_keyfile):
            errors["non_field_errors"].append(_(messages.HC_PWD_OR_KEYFILE))
        if not self.partial and ssh_passphrase and not ssh_keyfile:
            errors["ssh_passphrase"].append(_(messages.HC_NO_KEY_W_PASS))
        if errors:
            raise ValidationError(errors)
        return data
