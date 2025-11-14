"""HashiVault is used to read and write data securely using the HashiCorp Vault."""

import base64

import hvac
from django.conf import settings


class VaultClient:
    """Instantiate a HashiVault client for encryption and decryption of data."""

    def __init__(self):
        if settings.QUIPUCORDS_VAULT_ENABLED:
            self.vault_client = hvac.Client(
                url=settings.QUIPUCORDS_VAULT_ADDR,
                token=settings.QUIPUCORDS_VAULT_TOKEN,
                verify=settings.QUIPUCORDS_VAULT_SSL_VERIFY,
            )
        else:
            self.vault_client = None

    def encrypt(self, plaintext):
        """Encrypt plain text using Vault."""
        plaintext_bytes = (
            plaintext.encode("utf8") if isinstance(plaintext, str) else plaintext
        )
        plaintext_b64 = base64.urlsafe_b64encode(plaintext_bytes).decode("ascii")
        encrypted_response = self.vault_client.secrets.transit.encrypt_data(
            mount_point=settings.QUIPUCORDS_VAULT_MOUNT_POINT,
            name=settings.QUIPUCORDS_VAULT_ENCRYPTION_KEY,
            plaintext=plaintext_b64,
        )
        return encrypted_response["data"]["ciphertext"]

    def decrypt(self, key, ciphertext):
        """Decrypt encrypted data using Vault."""
        decrypted_response = self.vault_client.secrets.transit.decrypt_data(
            mount_point=settings.QUIPUCORDS_VAULT_MOUNT_POINT,
            name=settings.QUIPUCORDS_VAULT_ENCRYPTION_KEY,
            ciphertext=ciphertext,
        )
        decrypted_response_b64 = decrypted_response["data"]["plaintext"]
        return base64.urlsafe_b64decode(decrypted_response_b64).decode("utf-8")
