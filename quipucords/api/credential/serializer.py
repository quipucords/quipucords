"""Module for serializing all model object for database storage."""

import os

from django.utils.translation import gettext as _
from rest_framework.serializers import CharField, ValidationError, empty

from api import messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.common.util import check_for_existing_name
from api.models import Credential
from constants import DataSources
from utils import get_from_object_or_dict


def expand_filepath(filepath):
    """Expand the ssh_keyfile filepath if necessary."""
    if filepath is not None:
        expanded = os.path.abspath(
            os.path.normpath(os.path.expanduser(os.path.expandvars(filepath)))
        )
        return expanded
    return filepath


class CredentialSerializer(NotEmptySerializer):
    """Serializer for the Credential model."""

    name = CharField(required=True, max_length=64)
    username = CharField(required=False, max_length=64)
    password = CharField(
        required=False,
        max_length=1024,
        allow_null=True,
        style={"input_type": "password"},
    )
    auth_token = CharField(
        required=False,
        max_length=1024,
        allow_null=True,
        style={"input_type": "password"},
    )
    ssh_keyfile = CharField(required=False, max_length=1024, allow_null=True)
    ssh_passphrase = CharField(
        required=False,
        max_length=1024,
        allow_null=True,
        style={"input_type": "password"},
    )
    become_method = ValidStringChoiceField(
        required=False, choices=Credential.BECOME_METHOD_CHOICES
    )
    become_user = CharField(required=False, max_length=64)
    become_password = CharField(
        required=False,
        max_length=1024,
        allow_null=True,
        style={"input_type": "password"},
    )

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = "__all__"

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
        cred_type = get_from_object_or_dict(self.instance, attrs, "cred_type")

        if cred_type == DataSources.VCENTER:
            validated_data = self.validate_vcenter_cred(attrs)
        elif cred_type == DataSources.SATELLITE:
            validated_data = self.validate_satellite_cred(attrs)
        elif cred_type == DataSources.NETWORK:
            validated_data = self.validate_host_cred(attrs)
        elif cred_type == DataSources.OPENSHIFT:
            validated_data = self.validate_openshift_cred(attrs)
        else:
            raise ValidationError({"cred_type": messages.UNKNOWN_CRED_TYPE})
        return validated_data

    def create(self, validated_data):
        """Create host credential."""
        name = validated_data.get("name")
        check_for_existing_name(
            Credential.objects, name, _(messages.HC_NAME_ALREADY_EXISTS % name)
        )

        cred_type = validated_data.get("cred_type")
        become_method = validated_data.get("become_method")
        become_user = validated_data.get("become_user")

        if cred_type == DataSources.NETWORK and not become_method:
            # Set the default become_method to be sudo if not specified
            validated_data["become_method"] = Credential.BECOME_SUDO
        if cred_type == DataSources.NETWORK and not become_user:
            # Set the default become_user to root if not specified
            validated_data["become_user"] = Credential.BECOME_USER_DEFAULT

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

    def validate_host_cred(self, attrs):
        """Validate the attributes for host creds."""
        ssh_keyfile = "ssh_keyfile" in attrs and attrs["ssh_keyfile"]
        password = "password" in attrs and attrs["password"]
        ssh_passphrase = "ssh_passphrase" in attrs and attrs["ssh_passphrase"]
        username = "username" in attrs and attrs["username"]

        if not username and not self.partial:
            error = {"username": _(messages.HOST_USERNAME_CREDENTIAL)}
            raise ValidationError(error)

        if not (password or ssh_keyfile) and not self.partial:
            error = {"non_field_errors": [_(messages.HC_PWD_OR_KEYFILE)]}
            raise ValidationError(error)

        if password and ssh_keyfile:
            error = {"non_field_errors": [_(messages.HC_NOT_BOTH)]}
            raise ValidationError(error)

        if ssh_keyfile:
            keyfile = expand_filepath(ssh_keyfile)
            if not os.path.isfile(keyfile):
                error = {"ssh_keyfile": [_(messages.HC_KEY_INVALID % (ssh_keyfile))]}
                raise ValidationError(error)
            attrs["ssh_keyfile"] = keyfile

        if ssh_passphrase and not ssh_keyfile and not self.partial:
            error = {"ssh_passphrase": [_(messages.HC_NO_KEY_W_PASS)]}
            raise ValidationError(error)

        self._check_for_disallowed_fields(
            DataSources.NETWORK, attrs, messages.HOST_FIELD_NOT_ALLOWED
        )

        return attrs

    def validate_vcenter_cred(self, attrs):
        """Validate the attributes for vcenter creds."""
        # Required fields for vcenter
        if not self.partial:
            username = "username" in attrs and attrs["username"]
            password = "password" in attrs and attrs["password"]

            if not (password and username):
                error = {"non_field_errors": [_(messages.VC_PWD_AND_USERNAME)]}
                raise ValidationError(error)

        self._check_for_disallowed_fields(
            DataSources.VCENTER, attrs, messages.VC_FIELDS_NOT_ALLOWED
        )
        return attrs

    def validate_satellite_cred(self, attrs):
        """Validate the attributes for satellite creds."""
        # Required fields for satellite
        if not self.partial:
            username = "username" in attrs and attrs["username"]
            password = "password" in attrs and attrs["password"]

            if not (password and username):
                error = {"non_field_errors": [_(messages.SAT_PWD_AND_USERNAME)]}
                raise ValidationError(error)

        self._check_for_disallowed_fields(
            DataSources.SATELLITE,
            attrs,
            messages.SAT_FIELD_NOT_ALLOWED,
        )
        return attrs

    def validate_openshift_cred(self, attrs):
        """Validate the attributes for openshift credentials."""
        # Required field for OpenShift credential
        auth_token = get_from_object_or_dict(self.instance, attrs, "auth_token")

        if not auth_token:
            error = {"auth_token": [_(messages.OPENSHIFT_CRED_REQUIRED_FIELD)]}
            raise ValidationError(error)

        self._check_for_disallowed_fields(
            DataSources.OPENSHIFT, attrs, messages.OPENSHIFT_FIELD_NOT_ALLOWED
        )
        return attrs

    def _check_for_disallowed_fields(self, credential_type, attrs, message):
        """Check if forbidden fields are being passed to credentials."""
        required_fields_map = {
            DataSources.OPENSHIFT: {"id", "name", "cred_type", "auth_token"},
            DataSources.VCENTER: {
                "cred_type",
                "id",
                "name",
                "password",
                "username",
            },
            DataSources.SATELLITE: {
                "cred_type",
                "id",
                "name",
                "password",
                "username",
            },
            DataSources.NETWORK: {
                "become_method",
                "become_password",
                "become_user",
                "cred_type",
                "id",
                "name",
                "password",
                "ssh_keyfile",
                "ssh_passphrase",
                "username",
            },
        }

        complete_fields_map = set(self.fields.keys())
        not_allowed_fields = complete_fields_map - required_fields_map[credential_type]
        errors = {}
        for field in not_allowed_fields:
            if attrs.get(field):
                errors[field] = message
        if errors:
            raise ValidationError(errors)
