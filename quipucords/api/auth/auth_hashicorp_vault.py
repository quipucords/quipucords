"""Authentication support for HashiCorp Vault."""

import base64
import binascii
import tempfile
from contextlib import contextmanager
from logging import getLogger

import hvac
from django.conf import settings
from django.utils.translation import gettext as _
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

import api.messages
from api.secure_token.model import SecureToken

logger = getLogger(__name__)

# We support a single HashiCorp Vault server definition.
# This is a Singleton for the whole app so it's not associated to a Discovery user.

HASHICORP_VAULT_NAME = "hashicorp-vault-server"
HASHICORP_VAULT_TYPE = "hashicorp-vault"

HASHICORP_VAULT_CLIENT_CERT = "client_cert"
HASHICORP_VAULT_CLIENT_KEY = "client_key"
HASHICORP_VAULT_CA_CERT = "ca_cert"

HASHICORP_VAULT_SUPPORTED_CERT_FILES = [
    HASHICORP_VAULT_CLIENT_CERT,
    HASHICORP_VAULT_CLIENT_KEY,
    HASHICORP_VAULT_CA_CERT,
]


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


def hashicorp_vault_address(metadata) -> str:
    """Return the HashiCorp Vault Address."""
    address = metadata.get("address")
    port = metadata.get("port", settings.QUIPUCORDS_HASHICORP_VAULT_DEFAULT_PORT)
    return f"{address}:{port}"


def hashicorp_vault_url(metadata) -> str:
    """Return the HashiCorp Vault URL."""
    return f"https://{hashicorp_vault_address(metadata)}"


def decode_cert_from_content(cert_file_name, cert_file_content_b64) -> str | None:
    """Get the HashiCorp Vault decoded Cert file content."""
    if not cert_file_content_b64:
        return None
    try:
        cert_file_content = base64.b64decode(
            cert_file_content_b64, validate=True
        ).decode("utf-8")
        return cert_file_content
    except binascii.Error as err:
        raise ValueError(
            _(
                api.messages.HASHICORP_VAULT_FAILED_B64_DECODE_CERT
                % (cert_file_name, str(err))
            )
        )
    except UnicodeDecodeError as err:
        raise ValueError(
            _(
                api.messages.HASHICORP_VAULT_FAILED_DECODE_CERT
                % (cert_file_name, str(err))
            )
        )


def hashicorp_cert_file(cert_file_name, cert_file_content_b64) -> str | None:
    """Get the HashiCorp Vault decoded Cert file content."""
    if cert_file_content_b64:
        try:
            cert_file_content = decode_cert_from_content(
                cert_file_name, cert_file_content_b64
            )
            return cert_file_content
        except ValueError as err:
            logger.error(err)
    return None


@contextmanager
def hashicorp_vault_client(vault_token=None, metadata=None):
    """Create a Context for communicating with a HashiCorp Vault server."""
    # Example using this context manager for a HashiCorp Vault query:
    #
    #    with hashicorp_vault_client(vault_secure_token) as vault_client:
    #        aap_creds = vault_client.secrets.kv.v2.read_secret_version(
    #            path="aap/aap25server", mount_point="secret"
    #        )
    #     ...
    if vault_token:
        metadata = vault_token.metadata
    ssl_verify = metadata.get("ssl_verify", True)
    vault_url = hashicorp_vault_url(metadata)
    client_cert_content = hashicorp_cert_file(
        HASHICORP_VAULT_CLIENT_CERT, metadata.get(HASHICORP_VAULT_CLIENT_CERT, None)
    )
    client_key_content = hashicorp_cert_file(
        HASHICORP_VAULT_CLIENT_KEY, metadata.get(HASHICORP_VAULT_CLIENT_KEY, None)
    )
    ca_file_content = hashicorp_cert_file(
        HASHICORP_VAULT_CA_CERT, metadata.get(HASHICORP_VAULT_CA_CERT, None)
    )

    with (
        tempfile.NamedTemporaryFile(delete=True) as cert_file,
        tempfile.NamedTemporaryFile(delete=True) as key_file,
        tempfile.NamedTemporaryFile(delete=True) as ca_file,
    ):
        cert_file.write(client_cert_content.encode("utf-8"))
        cert_file.flush()
        key_file.write(client_key_content.encode("utf-8"))
        key_file.flush()

        if ssl_verify:
            ca_file.write(ca_file_content) and ca_file.flush()
            yield hvac.Client(
                url=vault_url,
                cert=(cert_file.name, key_file.name),
                verify=ca_file.name,
                timeout=settings.QUIPUCORDS_HASHICORP_VAULT_TIMEOUT,
            )
        else:
            yield hvac.Client(
                url=vault_url,
                cert=(cert_file.name, key_file.name),
                verify=False,
                timeout=settings.QUIPUCORDS_HASHICORP_VAULT_TIMEOUT,
            )


def hashicorp_vault_authenticate(vault_token=None, metadata=None) -> bool:
    """Authenticate to a HashiCorp Vault."""
    if vault_token:
        metadata = vault_token.metadata
    with hashicorp_vault_client(
        vault_token=vault_token, metadata=metadata
    ) as vault_client:
        vault_address = hashicorp_vault_address(metadata)
        try:
            if vault_client.is_authenticated():
                logger.debug(api.messages.HASHICORP_VAULT_AUTHENTICATED, vault_address)
                return True
            else:
                logger.error(
                    api.messages.HASHICORP_VAULT_FAILED_AUTHENTICATION, vault_address
                )
                return False
        except ConnectionError as err:
            logger.error(
                api.messages.HASHICORP_VAULT_CONNECTION_ERROR, vault_address, str(err)
            )
            raise HashiCorpVaultAuthError(
                _(
                    api.messages.HASHICORP_VAULT_CONNECTION_ERROR
                    % (vault_address, str(err))
                )
            )
        except BaseHTTPError as err:
            logger.error(
                api.messages.HASHICORP_VAULT_HTTP_ERROR, vault_address, str(err)
            )
            raise HashiCorpVaultAuthError(
                _(api.messages.HASHICORP_VAULT_HTTP_ERROR % (vault_address, str(err)))
            )
