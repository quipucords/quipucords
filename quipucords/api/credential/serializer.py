"""Module for serializing all model object for database storage."""

import os
from collections import defaultdict

from django.utils.translation import gettext as _
from rest_framework.serializers import ValidationError, empty

from api import messages
from api.common.serializer import NotEmptySerializer
from api.models import Credential, Source
from constants import ENCRYPTED_DATA_MASK, DataSources


def expand_filepath(filepath):
    """Expand the ssh_keyfile filepath if necessary."""
    if filepath is not None:
        expanded = os.path.abspath(
            os.path.normpath(os.path.expanduser(os.path.expandvars(filepath)))
        )
        return expanded
    return filepath


ENCRYPTED_FIELD_KWARGS = {"style": {"input_type": "password"}}


class RelatedSourceSerializer(NotEmptySerializer):
    """Serializer for Source objects related to Credential."""

    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = ["id", "name"]


class CredentialSerializer(NotEmptySerializer):
    """Base Serializer for the Credential model."""

    sources = RelatedSourceSerializer(many=True, read_only=True)

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

    # Instead of following DRF BaseSerializer.__new__ signature (cls, *args, **kwargs),
    # our __new__ method uses BaseSerializer.__init__ signature. This is OK, because:
    # A) class level __new__ just calls __init__ with the same *args, *kwargs [1];
    # B) DRF BaseSerializer.__new__ only modifies kwargs [3];
    #
    # References
    # [1]: https://docs.python.org/3/reference/datamodel.html#object.__new__
    # [2]: https://github.com/encode/django-rest-framework/blob/3.14.0/rest_framework/serializers.py#L121  # noqa: E501

    def __new__(
        cls, instance=None, data=empty, **kwargs
    ):  # pylint: disable=arguments-differ
        """Overloaded __new__ to return the appropriate serializer."""
        cred_type = cls._get_cred_type(instance, data)
        klass = cls._get_serializer_class(cred_type)
        return super().__new__(klass, instance=instance, data=data, **kwargs)

    @classmethod
    def _get_serializer_class(cls, cred_type):
        """Return the appropriate serializer based on 'cred_type'."""
        serializer_per_datasource = defaultdict(
            lambda: CredentialSerializer,
            {
                DataSources.NETWORK: NetworkCredentialSerializer,
                DataSources.OPENSHIFT: AuthTokenSerializer,
                DataSources.VCENTER: UsernamePasswordSerializer,
                DataSources.SATELLITE: UsernamePasswordSerializer,
            },
        )

        return serializer_per_datasource[cred_type]

    @classmethod
    def _get_cred_type(cls, instance, data):
        if isinstance(instance, Credential):
            return instance.cred_type
        if isinstance(data, dict):
            return data.get("cred_type")
        return None

    def __init__(self, instance=None, data=empty, **kwargs):
        """Customize class initialization."""
        if instance and isinstance(data, dict):
            # assume cred_type == instance.cred_type if not provided
            # this is only required to avoid breaking current functionality
            # that was treating 'cred_type' as optional for updates and required for
            # credential creation
            data.setdefault("cred_type", instance.cred_type)
        super().__init__(instance=instance, data=data, **kwargs)

    def validate_cred_type(self, cred_type):
        """Validate cred_type field."""
        if self.instance and cred_type != self.instance.cred_type:
            raise ValidationError(_(messages.CRED_TYPE_NOT_ALLOWED_UPDATE))
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

    def to_representation(self, instance):
        """Overload DRF representation method to mask encrypted fields."""
        _data = super().to_representation(instance)
        for field in Credential.ENCRYPTED_FIELDS:
            if field in _data:
                _data[field] = ENCRYPTED_DATA_MASK
        return _data


class AuthTokenSerializer(CredentialSerializer):
    """Serializer for credentials that require only auth_token."""

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = ["id", "name", "cred_type", "auth_token", "sources"]
        extra_kwargs = {
            "auth_token": {"required": True, **ENCRYPTED_FIELD_KWARGS},
        }


class UsernamePasswordSerializer(CredentialSerializer):
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
            "sources",
        ]
        extra_kwargs = {
            "password": {"required": True, **ENCRYPTED_FIELD_KWARGS},
            "username": {"required": True},
        }


class NetworkCredentialSerializer(CredentialSerializer):
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
            "sources",
        ]
        extra_kwargs = {
            "become_method": {"default": Credential.BECOME_SUDO},
            "become_password": ENCRYPTED_FIELD_KWARGS,
            "become_user": {"default": Credential.BECOME_USER_DEFAULT},
            "password": ENCRYPTED_FIELD_KWARGS,
            "ssh_passphrase": ENCRYPTED_FIELD_KWARGS,
            "username": {"required": True},
        }

    def validate_ssh_keyfile(self, ssh_keyfile):
        """Validate ssh_keyfile field."""
        if ssh_keyfile is None:
            return None
        keyfile = expand_filepath(ssh_keyfile)
        if not os.path.isfile(keyfile):
            raise ValidationError(_(messages.HC_KEY_INVALID % ssh_keyfile))
        return keyfile

    def validate(self, attrs):
        """Validate fields that need to be evaluated together."""
        data = super().validate(attrs)
        errors = defaultdict(list)
        password = data.get("password")
        ssh_keyfile = data.get("ssh_keyfile")
        ssh_passphrase = data.get("ssh_passphrase")
        instance_ssh_key = getattr(self.instance, "ssh_keyfile", None)

        if password and ssh_keyfile:
            errors["non_field_errors"].append(_(messages.HC_NOT_BOTH))
        if not self.partial and not (password or ssh_keyfile):
            errors["non_field_errors"].append(_(messages.HC_PWD_OR_KEYFILE))
        if ssh_passphrase and not (ssh_keyfile or instance_ssh_key):
            errors["ssh_passphrase"].append(_(messages.HC_NO_KEY_W_PASS))
        if errors:
            raise ValidationError(errors)
        if self.instance:
            self.prepare_data_for_update(data)
        return data

    @classmethod
    def prepare_data_for_update(cls, data: dict):
        """Transform validated data prior to an update."""
        password = data.get("password")
        ssh_keyfile = data.get("ssh_keyfile")
        # a credential should have either password or ssh_key
        # (this method assumes the premise that data is properly validated)
        if password:
            data["ssh_keyfile"] = None
        elif ssh_keyfile:
            data["password"] = None


class ReadOnlyCredentialSerializer(NotEmptySerializer):
    """A specialized serializer for scanner needs."""

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = "__all__"
        read_only_fields = [field.name for field in Credential._meta.fields]
