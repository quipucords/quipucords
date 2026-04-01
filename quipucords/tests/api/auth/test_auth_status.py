"""Test the Auth status API."""

from datetime import UTC, datetime, timedelta

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.common.enumerators import AuthStatus
from tests.utils.auth import create_lightspeed_secure_token


@pytest.mark.django_db
class TestLightspeedAuthStatus:
    """Test the Lightspeed status functionality of the auth module."""

    def test_unauthenticated_user(self, client_logged_out):
        """Test unauthenticated users cannot get status without authentication."""
        response = client_logged_out.get(reverse("v2:lightspeed-auth-status"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_with_missing_auth(self, client_logged_in, faker):
        """Test users get a missing status if not authorized with Lightspeed."""
        response = client_logged_in.get(reverse("v2:lightspeed-auth-status"))
        assert response.ok
        response_json = response.json()
        assert response_json["status"] == AuthStatus.MISSING.value

    def test_with_valid_auth(
        self, client_logged_in, qpc_user_simple, lightspeed_user_metadata
    ):
        """Test users get a valid status if the Lightspeed SecureToken is valid."""
        lightspeed_user_token = create_lightspeed_secure_token(
            qpc_user_simple, lightspeed_user_metadata
        )

        response = client_logged_in.get(reverse("v2:lightspeed-auth-status"))
        assert response.ok
        response_json = response.json()
        assert response_json["status"] == AuthStatus.VALID.value
        assert response_json["metadata"] == lightspeed_user_token.metadata

    def test_with_expired_auth(
        self, client_logged_in, qpc_user_simple, lightspeed_user_metadata, faker
    ):
        """Test users get an expired status if the Lightspeed SecureToken is expired."""
        lightspeed_user_token = create_lightspeed_secure_token(
            qpc_user_simple, lightspeed_user_metadata
        )
        past_time = datetime.now(UTC) - timedelta(hours=4)
        lightspeed_user_token.expires_at = past_time
        lightspeed_user_token.save()

        expected_metadata = lightspeed_user_token.metadata.copy()
        expected_metadata["status"] = AuthStatus.EXPIRED.value
        expected_metadata["status_reason"] = messages.LIGHTSPEED_TOKEN_EXPIRED

        response = client_logged_in.get(reverse("v2:lightspeed-auth-status"))
        assert response.ok
        response_json = response.json()
        assert response_json["status"] == AuthStatus.EXPIRED.value
        assert response_json["metadata"] == expected_metadata

    def test_failed_lightspeed_login(
        self,
        client_logged_in,
        qpc_user_simple,
        lightspeed_user_metadata,
    ):
        """Test a failed Lightspeed status returns error in the Error detail."""
        token_metadata = lightspeed_user_metadata | {
            "status": AuthStatus.FAILED.value,
            "status_reason": messages.LIGHTSPEED_INVALID_TOKEN,
        }
        create_lightspeed_secure_token(qpc_user_simple, token_metadata)

        response = client_logged_in.get(reverse("v2:lightspeed-auth-status"))
        assert response.ok
        response_json = response.json()
        assert response_json["status"] == AuthStatus.FAILED.value
        assert response_json["metadata"] == token_metadata
