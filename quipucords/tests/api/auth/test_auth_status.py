"""Test the Auth status API."""

from datetime import UTC, datetime, timedelta

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.auth.auth_lightspeed import LIGHTSPEED_NAME, LIGHTSPEED_TYPE
from api.auth.utils import AuthError
from api.auth.view import SUPPORTED_AUTH_TYPES_STR
from api.common.enumerators import AuthStatus
from api.secure_token.model import SecureToken

LIGHTSPEED_AUTH_TYPE = "lightspeed"


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


@pytest.mark.django_db
class TestAuthStatus:
    """Test the status functionality of the auth module."""

    def test_unauthenticated_user(self, client_logged_out):
        """Test unauthenticated users cannot get status without authentication."""
        response = client_logged_out.get(reverse("v2:auth-status"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_missing_auth_type(self, client_logged_in):
        """Test users cannot get status without specifying an auth_type."""
        response = client_logged_in.get(reverse("v2:auth-status"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert messages.AUTH_MUST_SPECIFY_TYPE in response_json["detail"]

    def test_invalid_auth_type(self, client_logged_in, faker):
        """Test users cannot get status with an invalid auth_type."""
        invalid_auth_type = faker.slug()
        query_params = {"auth_type": invalid_auth_type}
        response = client_logged_in.get(
            reverse("v2:auth-status", query=query_params),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        expected_error = messages.AUTH_INVALID_AUTH_TYPE % {
            "auth_type": invalid_auth_type,
            "supported_auth_types": SUPPORTED_AUTH_TYPES_STR,
        }
        assert expected_error in response_json["detail"]

    def test_with_missing_auth(self, client_logged_in, faker):
        """Test users get a missing status if not authorized with Lightspeed."""
        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.get(
            reverse("v2:auth-status", query=query_params),
        )
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

        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.get(
            reverse("v2:auth-status", query=query_params),
        )
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

        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.get(
            reverse("v2:auth-status", query=query_params),
        )
        assert response.ok
        response_json = response.json()
        assert response_json["status"] == AuthStatus.EXPIRED.value
        assert response_json["metadata"] == expected_metadata

    def test_failed_lightspeed_login(
        self,
        mocker,
        client_logged_in,
    ):
        """Test a failed Lightspeed status returns error in the Error detail."""
        raised_exception = "Lightspeed Auth status test exception"
        mock_auth_status = mocker.patch(
            "api.auth.view.lightspeed_auth_status",
        )
        mock_auth_status.side_effect = AuthError(raised_exception)

        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.get(
            reverse("v2:auth-status", query=query_params),
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_json = response.json()
        assert response_json["detail"] == raised_exception
