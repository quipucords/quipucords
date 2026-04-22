"""Test the Auth logout API."""

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.auth.lightspeed.auth import (
    get_lightspeed_secure_token,
    get_or_create_lightspeed_secure_token,
)


@pytest.mark.django_db
class TestAuthLightspeedLogout:
    """Test the logout functionality of the auth module."""

    def test_unauthenticated_user(self, client_logged_out):
        """Test users cannot log out without authentication."""
        response = client_logged_out.post(reverse("v2:lightspeed-auth-logout"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_lightspeed_logout(
        self,
        qpc_user_simple,
        client_logged_in,
        lightspeed_auth_response,
    ):
        """Test users can do a Lightspeed logout."""
        _ = get_or_create_lightspeed_secure_token(qpc_user_simple)
        response = client_logged_in.post(reverse("v2:lightspeed-auth-logout"))
        assert response.ok
        expected_response = {
            "status": "successful",
            "status_reason": messages.LIGHTSPEED_LOGOUT_SUCCESSFUL,
        }
        response_json = response.json()
        assert response_json == expected_response
        assert get_lightspeed_secure_token(qpc_user_simple) is None

    def test_lightspeed_already_logout(
        self,
        qpc_user_simple,
        client_logged_in,
        lightspeed_auth_response,
    ):
        """Test users can do a Lightspeed logout."""
        response = client_logged_in.post(reverse("v2:lightspeed-auth-logout"))
        assert response.ok
        expected_response = {
            "status": "successful",
            "status_reason": messages.LIGHTSPEED_ALREADY_LOGGED_OUT,
        }
        response_json = response.json()
        assert response_json == expected_response
        assert get_lightspeed_secure_token(qpc_user_simple) is None
