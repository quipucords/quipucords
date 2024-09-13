"""Credential API/model serializers."""

from collections import defaultdict

from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings as drf_settings

from api import messages
from api.common.serializer import NotEmptySerializer
from api.credential.model import Credential
from api.source.model import Source

ENCRYPTED_FIELD_KWARGS = {
    "style": {"input_type": "password"},
    "write_only": True,
    "trim_whitespace": False,
}
NON_FIELD_ERRORS_KEY = drf_settings.NON_FIELD_ERRORS_KEY


class RelatedSourceSerializer(NotEmptySerializer):
    """Serializer for Source objects related to Credential."""

    class Meta:
        """Metadata for the serializer."""

        model = Source
        fields = ["id", "name"]


class CredentialSerializerV2(ModelSerializer):
    """Serializer for the Credential model."""

    sources = RelatedSourceSerializer(many=True, read_only=True)

    auth_type = SerializerMethodField()
    has_auth_token = SerializerMethodField()
    has_password = SerializerMethodField()
    has_ssh_key = SerializerMethodField()
    has_ssh_passphrase = SerializerMethodField()
    has_become_password = SerializerMethodField()

    class Meta:
        """Metadata for the serializer."""

        model = Credential
        fields = "__all__"
        extra_kwargs = {
            "auth_token": ENCRYPTED_FIELD_KWARGS,
            "become_password": ENCRYPTED_FIELD_KWARGS,
            "password": ENCRYPTED_FIELD_KWARGS,
            "ssh_key": ENCRYPTED_FIELD_KWARGS,
            "ssh_keyfile": {"read_only": True},
            "ssh_passphrase": ENCRYPTED_FIELD_KWARGS,
        }
        optional_type_specific_fields = {
            "auth_token",
            "become_method",
            "become_password",
            "become_user",
            "password",
            "ssh_key",
            "ssh_keyfile",
            "ssh_passphrase",
            "username",
        }

    def get_auth_type(self, credential: Credential) -> str:
        """Determine a credential's authentication type."""
        if credential.auth_token:
            return "auth_token"
        elif credential.password:
            return "password"
        elif credential.ssh_key:
            return "ssh_key"
        elif credential.ssh_keyfile:
            return "ssh_keyfile"
        return "unknown"

    def get_has_auth_token(self, credential: Credential) -> bool:
        """Determine if credential has a non-empty auth token."""
        return credential.auth_token is not None and credential.auth_token != ""

    def get_has_password(self, credential: Credential) -> bool:
        """Determine if credential has a non-empty password."""
        return credential.password is not None and credential.password != ""

    def get_has_ssh_key(self, credential: Credential) -> bool:
        """Determine if credential has a non-empty ssh_key."""
        return credential.ssh_key is not None and credential.ssh_key != ""

    def get_has_ssh_passphrase(self, credential: Credential) -> bool:
        """Determine if credential has a non-empty ssh_passphrase."""
        return credential.ssh_passphrase is not None and credential.ssh_passphrase != ""

    def get_has_become_password(self, credential: Credential) -> bool:
        """Determine if credential has a non-empty become_password."""
        return (
            credential.become_password is not None and credential.become_password != ""
        )

    def validate_cred_type(self, cred_type):
        """Validate cred_type field."""
        if self.instance and cred_type != self.instance.cred_type:
            raise ValidationError(messages.CRED_TYPE_NOT_ALLOWED_UPDATE)
        return cred_type

    def get_fields_to_clear(self) -> set:
        """Get a set of unwanted field names to clear during validation."""
        if self.Meta.fields == ["__all__"]:
            return set()  # because we can't do anything with the generic "all" token
        all_fields = set(CredentialSerializerV2.Meta.optional_type_specific_fields)
        my_type_fields = set(self.Meta.fields)
        fields_to_clear = all_fields - my_type_fields
        return fields_to_clear

    def validate(self, attrs: dict) -> dict:
        """
        Perform validation with the side effect of clearing unwanted fields.

        Why would you want this? Consider the use case for OpenShift-type Credentials
        that must use either an auth_token or a username and password combination but
        never both. When saving partial/PATCH updates to an existing instance, if the
        user changes from one auth type to the other, we do not require the client to
        set empty/null values for the other fields. Instead, we clear the fields used
        by the other type on the user's behalf. This method performs that clearing on
        the incoming attrs data being validated.
        """
        attrs = super().validate(attrs)
        fields_to_clear = self.get_fields_to_clear()
        attrs.update({field: None for field in fields_to_clear})
        return attrs

    def create(self, *args, **kwargs) -> Credential:
        """
        Protect against invoking CredentialSerializerV2.create directly.

        Model write operations must happen through type-specific subclasses.
        """
        if self.__class__ == CredentialSerializerV2:
            raise NotImplementedError("Use type-specific serializer for 'create'.")
        return super().create(*args, **kwargs)

    def update(self, *args, **kwargs) -> Credential:
        """
        Protect against invoking CredentialSerializerV2.update directly.

        Model write operations must happen through type-specific subclasses.
        """
        if self.__class__ == CredentialSerializerV2:
            raise NotImplementedError("Use type-specific serializer for 'update'.")
        return super().update(*args, **kwargs)


class AuthTokenSerializerV2(CredentialSerializerV2):
    """
    Credential serializer that requires auth_token.

    This serializer should be used only for Credential write operations.
    The Meta class defines only the fields required for writing to the model.
    """

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = ["auth_token", "cred_type", "name"]
        extra_kwargs = {
            "auth_token": {
                "required": True,
                "allow_blank": False,
                **ENCRYPTED_FIELD_KWARGS,
            },
        }


class UsernamePasswordSerializerV2(CredentialSerializerV2):
    """
    Credential serializer that requires username and password.

    This serializer should be used only for Credential write operations.
    The Meta class defines only the fields required for writing to the model.
    """

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = ["cred_type", "name", "password", "username"]
        extra_kwargs = {
            "password": {
                "required": True,
                "allow_blank": False,
                **ENCRYPTED_FIELD_KWARGS,
            },
            "username": {"required": True, "allow_blank": False},
        }


class SshCredentialSerializerV2(CredentialSerializerV2):
    """
    Credential serializer that requires fields for an SSH connection.

    This serializer should be used only for Credential write operations.
    The Meta class defines only the fields required for writing to the model.
    """

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = [
            "become_method",
            "become_password",
            "become_user",
            "cred_type",
            "name",
            "password",
            "ssh_key",
            "ssh_keyfile",
            "ssh_passphrase",
            "username",
        ]
        extra_kwargs = {
            "become_method": {"default": Credential.BECOME_SUDO},
            "become_password": ENCRYPTED_FIELD_KWARGS,
            "become_user": {"default": Credential.BECOME_USER_DEFAULT},
            "password": ENCRYPTED_FIELD_KWARGS,
            "ssh_key": ENCRYPTED_FIELD_KWARGS,
            "ssh_keyfile": {"read_only": True},
            "ssh_passphrase": ENCRYPTED_FIELD_KWARGS,
            "username": {"required": True},
        }

    def validate(self, attrs: dict):
        """Run validations that require more than one field."""
        attrs = super().validate(attrs)
        has_password, has_ssh_key = self._has_password_or_ssh_key(attrs)

        errors = defaultdict(list)
        if has_password and has_ssh_key:
            errors[NON_FIELD_ERRORS_KEY].append(messages.HC_PWD_NOT_WITH_KEY)
        if not has_password and not has_ssh_key:
            errors[NON_FIELD_ERRORS_KEY].append(messages.HC_PWD_OR_KEY)
        if attrs.get("ssh_passphrase") and not has_ssh_key:
            errors["ssh_passphrase"].append(messages.HC_NO_KEY_W_PASS)
        if errors:
            raise ValidationError(errors)

        # Clear unspecified attributes to ensure data integrity
        # in case this request effectively changes the auth type.
        if has_password:
            attrs["ssh_key"] = None
            attrs["ssh_passphrase"] = None
        elif has_ssh_key:
            attrs["password"] = None
        if attrs.get("ssh_passphrase") == "":
            # Converts empty string to None because it should be not-empty if set.
            attrs["ssh_passphrase"] = None
        if has_password or has_ssh_key:
            attrs["ssh_keyfile"] = None

        return attrs

    def _has_password_or_ssh_key(self, attrs: dict) -> tuple[bool, bool]:
        """
        Detect if input data has password and/or ssh_key.

        Returns a tuple of booleans: has_password and has_ssh_key in this order.
        """
        has_password = bool(attrs.get("password"))
        has_ssh_key = bool(attrs.get("ssh_key"))

        # self.partial means PATCH, so it's OK to infer from instance
        if self.partial and not has_password and not has_ssh_key:
            has_password = bool(getattr(self.instance, "password"))
            has_ssh_key = bool(getattr(self.instance, "ssh_key"))

        return has_password, has_ssh_key


class AuthTokenOrUserPassSerializerV2(CredentialSerializerV2):
    """
    Credential serializer that requires either username and password or auth_token.

    This serializer should be used only for Credential write operations.
    The Meta class defines only the fields required for writing to the model.
    """

    class Meta:
        """Serializer configuration."""

        model = Credential
        fields = [
            "cred_type",
            "name",
            "password",
            "username",
            "auth_token",
        ]
        extra_kwargs = {
            "password": ENCRYPTED_FIELD_KWARGS,
            "auth_token": ENCRYPTED_FIELD_KWARGS,
        }

    def validate(self, attrs: dict):
        """Run validations that require more than one field."""
        attrs = super().validate(attrs)
        has_user_or_pass, has_auth_token = self._get_user_pass_or_auth_token(attrs)

        if not has_auth_token and not has_user_or_pass:
            raise ValidationError(messages.TOKEN_OR_USER_PASS)

        if has_auth_token and has_user_or_pass:
            raise ValidationError(messages.TOKEN_OR_USER_PASS_NOT_BOTH)

        # defer the rest of the validation to specialized serializers
        validator_class = (
            AuthTokenSerializerV2 if has_auth_token else UsernamePasswordSerializerV2
        )
        validator = validator_class(self.instance, data=attrs, partial=self.partial)
        validator.is_valid(raise_exception=True)
        data = validator.validated_data
        return data

    def _get_user_pass_or_auth_token(self, attrs: dict) -> tuple[bool, bool]:
        """
        Detect if input data has username/password and/or auth token.

        Returns a tuple of booleans: has_user_or_pass and has_auth_token in this order.
        """
        has_user_or_pass = bool(attrs.get("password") or attrs.get("username"))
        has_auth_token = bool(attrs.get("auth_token"))
        # self.partial means PATCH, so it's OK to infer from instance
        if self.partial and not has_auth_token and not has_user_or_pass:
            has_user_or_pass = bool(
                getattr(self.instance, "password") or getattr(self.instance, "username")
            )
            has_auth_token = bool(getattr(self.instance, "auth_token"))
        return has_user_or_pass, has_auth_token
