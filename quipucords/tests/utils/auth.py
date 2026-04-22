"""Helpers for auth endpoints."""

from datetime import UTC, datetime, timedelta

from api.auth.lightspeed.auth import (
    LIGHTSPEED_NAME,
    LIGHTSPEED_TYPE,
)
from api.common.enumerators import AuthStatus
from api.secure_token.model import SecureToken


def create_lightspeed_secure_token(user, user_metadata):
    """Create a valid lightspeed authentication token that expires in the future."""
    future_time = datetime.now(UTC) + timedelta(hours=4)
    lightspeed_user_metadata = {
        "status": AuthStatus.VALID.value,
        "status_reason": "",
    } | user_metadata
    lightspeed_secure_token = SecureToken.objects.create(
        name=LIGHTSPEED_NAME,
        token_type=LIGHTSPEED_TYPE,
        user=user,
        metadata=lightspeed_user_metadata,
        expires_at=future_time,
    )
    lightspeed_secure_token.refresh_from_db()
    return lightspeed_secure_token
