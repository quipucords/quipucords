"""Test the Auth login API."""

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.auth.auth_lightspeed import LightspeedAuthError
from api.auth.view import SUPPORTED_AUTH_TYPES_STR
from api.common.enumerators import AuthStatus

LIGHTSPEED_AUTH_TYPE = "lightspeed"


@pytest.mark.django_db
class TestAuthLogin:
    """Test the login functionality of the auth module."""

    def test_unauthenticated_user(self, client_logged_out):
        """Test unauthenticated users cannot log in without authentication."""
        response = client_logged_out.post(reverse("v2:auth-login"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert "Authentication credentials were not provided" in response_json["detail"]

    def test_missing_auth_type(self, client_logged_in):
        """Test users cannot log in without specifying an auth_type."""
        response = client_logged_in.post(reverse("v2:auth-login"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert messages.AUTH_MUST_SPECIFY_TYPE in response_json["detail"]

    def test_invalid_auth_type(self, client_logged_in, faker):
        """Test users cannot log in with an invalid auth_type."""
        invalid_auth_type = faker.slug()
        query_params = {"auth_type": invalid_auth_type}
        response = client_logged_in.post(
            reverse("v2:auth-login", query=query_params),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        expected_error = messages.AUTH_INVALID_AUTH_TYPE % {
            "auth_type": invalid_auth_type,
            "supported_auth_types": SUPPORTED_AUTH_TYPES_STR,
        }
        assert expected_error in response_json["detail"]

    def test_lightspeed_login(
        self,
        mocker,
        client_logged_in,
        lightspeed_auth_response,
    ):
        """Test users can request a Lightspeed login."""
        mocker.patch(
            "api.auth.auth_lightspeed.lightspeed_request_auth",
            return_value=lightspeed_auth_response,
        )
        mock_wait_for_authorization = mocker.patch(
            "api.auth.auth_lightspeed.lightspeed_wait_for_authorization"
        )
        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.post(
            reverse("v2:auth-login", query=query_params),
        )
        assert response.ok
        expected_response = {
            "status": AuthStatus.PENDING.value,
            "user_code": lightspeed_auth_response["user_code"],
            "verification_uri": lightspeed_auth_response["verification_uri"],
            "verification_uri_complete": lightspeed_auth_response[
                "verification_uri_complete"
            ],
        }
        response_json = response.json()
        assert response_json == expected_response
        mock_wait_for_authorization.delay.assert_called_once_with(
            mocker.ANY,
            lightspeed_auth_response["device_code"],
            lightspeed_auth_response["interval"],
            lightspeed_auth_response["expires_in"],
        )

    def test_failed_lightspeed_login(
        self,
        mocker,
        client_logged_in,
    ):
        """Test a failed Lightspeed request returns error in the Error detail."""
        raised_exception = "Lightspeed Auth request test exception"
        mock_request_auth = mocker.patch(
            "api.auth.auth_lightspeed.lightspeed_request_auth",
        )
        mock_request_auth.side_effect = LightspeedAuthError(raised_exception)

        query_params = {"auth_type": LIGHTSPEED_AUTH_TYPE}
        response = client_logged_in.post(
            reverse("v2:auth-login", query=query_params),
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_json = response.json()
        assert response_json["detail"] == raised_exception
