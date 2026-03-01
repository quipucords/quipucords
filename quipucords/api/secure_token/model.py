"""Defines the SecureToken Models used with the API application."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from api.common.models import BaseModel
from api.encrypted_charfield import EncryptedCharField
from quipucords.user import User


class SecureToken(BaseModel):
    """Model for storing secure tokens."""

    INSIGHTS = "insights-jwt"

    TOKEN_TYPES = ((INSIGHTS, INSIGHTS),)

    name = models.CharField(max_length=64, null=False, blank=False)
    token_type = models.CharField(
        max_length=32, choices=TOKEN_TYPES, null=False, blank=False
    )

    # SecureToken can be optionally user bound
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Note: rh_jwt tokens can easily reach 3K, with Ansible encryption possibly
    #       quadrupling the size, we'll size up the token on the safe side, the
    #       PostgresDB will only allocate what it needs. worst case is a default 8K
    #       header size limit times 4 (should never be as the header size limit
    #       is for all headers).
    token = EncryptedCharField(max_length=32768, null=True, blank=True)

    metadata = EncryptedCharField(max_length=4096, null=True, blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)
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
