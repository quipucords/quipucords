"""Authentication support for HashiCorp Vault."""

from logging import getLogger

from api.secure_token.model import SecureToken

logger = getLogger(__name__)

# We support a single HashiCorp Vault server definition.
# This is a Singleton for the whole app so it's not associated to a Discovery user.

HASHICORP_VAULT_NAME = "hashicorp-vault-server"
HASHICORP_VAULT_TYPE = "hashicorp-vault"


class HashiCorpVaultAuthError(Exception):
    """Class for HashiCorp Vault authentication."""

    def __init__(self, message, *args):
        """Take message as mandatory attribute."""
        super().__init__(message, *args)
        self.message = message


def get_hashicorp_vault_token() -> SecureToken | None:
    """Get the HashiCorp Vault SecureToken, None if it does not exist."""
    return SecureToken.objects.filter(
        name=HASHICORP_VAULT_NAME, token_type=HASHICORP_VAULT_TYPE
    ).first()


def delete_hashicorp_vault_token() -> None:
    """Delete a HashiCorp Vault SecureToken."""
    hashicorp_vault_token = get_hashicorp_vault_token()
    if hashicorp_vault_token:
        hashicorp_vault_token.delete()


def get_or_create_hashicorp_vault_token() -> SecureToken:
    """Get a HashiCorp Vault SecureToken."""
    secure_token, created = SecureToken.objects.get_or_create(
        name=HASHICORP_VAULT_NAME, token_type=HASHICORP_VAULT_TYPE
    )
    if created:
        logger.debug(
            f"New {secure_token.token_type} Token {secure_token.name}"
            f" created, Token id: {secure_token.id}"
        )
    return secure_token
