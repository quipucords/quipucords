"""Defines the SecureToken Models used with the API application."""

from datetime import UTC, datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from api.common.models import BaseModel
from api.encrypted_fields import EncryptedCharField, EncryptedDictField


class SecureToken(BaseModel):
    """Model for storing secure tokens."""

    INSIGHTS = "insights-jwt"

    TOKEN_TYPES = ((INSIGHTS, INSIGHTS),)

    name = models.CharField(max_length=64, null=False, blank=False)
    token_type = models.CharField(
        max_length=32, choices=TOKEN_TYPES, null=False, blank=False
    )

    # SecureToken can be optionally user bound
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

    # Note: rh_jwt tokens can easily reach 3K, with Ansible encryption possibly
    #       quadrupling the size, we'll size up the token on the safe side, the
    #       PostgresDB will only allocate what it needs. worst case is a default 8K
    #       header size limit times 4 (should never be as the header size limit
    #       is for all headers).
    token = EncryptedCharField(max_length=32768, null=True, blank=True)

    metadata = EncryptedDictField(max_length=4096, null=True, blank=True)

    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Metadata for the SecureToken model."""

        verbose_name = _("Secure Token")
        verbose_name_plural = _("Secure Tokens")

        constraints = [
            # System wide secure token name uniqueness
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(user__isnull=True),
                name="unique_secure_token_name",
            ),
            # User bound secure token name uniqueness
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_user_secure_token_name"
            ),
        ]

    def save(self, *args, **kwargs):
        """Save the SecureToken object."""
        self.full_clean()  # Enforce model-level integrity
        super().save(*args, **kwargs)

    def clear_expiration(self):
        """Clear the expiration of the SecureToken object so it won't expire."""
        self.expires_at = None
        self.save()

    def set_expiration(self, expires_at: datetime):
        """Set the expiration of the SecureToken object."""
        self.expires_at = expires_at
        self.save()

    def is_expired(self) -> bool:
        """Return True if the SecureToken is expired."""
        if not self.expires_at:  # default is no expiration
            return False
        if datetime.now(UTC) >= self.expires_at:
            return True
        return False
