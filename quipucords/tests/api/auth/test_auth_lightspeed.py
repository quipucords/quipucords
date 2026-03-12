"""Test the Auth Lightspeed methods."""

import http

import pytest
from django.conf import settings
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError as BaseHTTPError

from api import messages
from api.auth.auth_lightspeed import (
    DEVICE_AUTH_ENDPOINT_KEY,
    OPENID_CONFIG_ENDPOINT,
    AuthStatus,
    LightspeedAuthError,
    get_or_create_lightspeed_secure_token,
    get_sso_endpoint,
    lightspeed_request_auth,
    lightspeed_wait_for_authorization,
    update_secure_token_metadata,
)
from api.auth.utils import decode_jwt


@pytest.mark.django_db
class TestAuthSecureToken:
    """Test the Auth SecureToken functions."""

    def test_update_secure_token_metadata(
        self, qpc_user_simple, client_logged_in, jwt_payload_dict, test_jwt
    ):
        """Test that a JWT is properly decoded and SecureToken metadata updated."""
        secure_token = get_or_create_lightspeed_secure_token(user=qpc_user_simple)
        decoded_lightspeed_jwt = decode_jwt(test_jwt)
        update_secure_token_metadata(secure_token, decoded_lightspeed_jwt)
        expected_metadata = {
            "org_id": jwt_payload_dict["organization"]["id"],
            "account_number": jwt_payload_dict["organization"]["account_number"],
            "username": jwt_payload_dict["preferred_username"],
            "first_name": jwt_payload_dict["given_name"],
            "last_name": jwt_payload_dict["family_name"],
            "email": jwt_payload_dict["email"],
        }
        secure_token.refresh_from_db()
        assert secure_token.metadata == expected_metadata

    def test_update_secure_token_expiration(
        self, qpc_user_simple, client_logged_in, test_jwt
    ):
        """Test that a JWT is properly decoded and SecureToken expiration is set."""
        secure_token = get_or_create_lightspeed_secure_token(user=qpc_user_simple)
        decoded_lightspeed_jwt = decode_jwt(test_jwt)
        update_secure_token_metadata(secure_token, decoded_lightspeed_jwt)
        secure_token.refresh_from_db()
        assert secure_token.expires_at == decoded_lightspeed_jwt["expires_at"]


@pytest.mark.django_db
class TestAuthSSO:
    """Test the Auth SSO Endpoint functions."""

    def test_get_sso_endpoint(self, faker, requests_mock):
        """Test the get_sso_endpoint method retrieves the SSO endpoints."""
        lightspeed_sso_server = settings.QUIPUCORDS_LIGHTSPEED_SSO_HOST
        url = f"https://{lightspeed_sso_server}{OPENID_CONFIG_ENDPOINT}"
        expected_endpoint = faker.url()
        config_endpoint_response = {DEVICE_AUTH_ENDPOINT_KEY: expected_endpoint}
        requests_mock.get(url, status_code=200, json=config_endpoint_response)

        device_auth_endpoint = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        assert device_auth_endpoint == expected_endpoint

    def test_get_sso_endpoint_connection_error(self, mocker):
        """Test the get_sso_endpoint method handles Connection Errors."""
        err_message = "Error connecting to the SSO server"
        mock_get_sso_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.get")
        mock_get_sso_endpoint.side_effect = ConnectionError(err_message)
        with pytest.raises(ConnectionError) as exception_error:
            _ = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        assert err_message in str(exception_error.value)

    def test_get_sso_endpoint_http_error(self, mocker):
        """Test the get_sso_endpoint method handles BaseHTTP Errors."""
        err_message = "BaseHTTPError connecting to the SSO server"
        mock_get_sso_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.get")
        mock_get_sso_endpoint.side_effect = BaseHTTPError(err_message)
        with pytest.raises(BaseHTTPError) as exception_error:
            _ = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        assert err_message in str(exception_error.value)

    def test_get_sso_endpoint_query_failed(self, faker, requests_mock):
        """Test the get_sso_endpoint handles missing SSO endpoints."""
        lightspeed_sso_server = settings.QUIPUCORDS_LIGHTSPEED_SSO_HOST
        url = f"https://{lightspeed_sso_server}{OPENID_CONFIG_ENDPOINT}"
        config_endpoint_response = {faker.slug(): faker.url()}
        requests_mock.get(url, status_code=200, json=config_endpoint_response)

        with pytest.raises(LightspeedAuthError) as exception_info:
            _device_auth_endpoint = get_sso_endpoint(DEVICE_AUTH_ENDPOINT_KEY)
        assert messages.LIGHTSPEED_SSO_QUERY_FAILED % DEVICE_AUTH_ENDPOINT_KEY in str(
            exception_info.value
        )


class TestLightspeedRequestAuth:
    """Test initiating the Lightspeed device authorization workflow."""

    def test_successful_request(self, mocker, lightspeed_auth_response, faker):
        """Test the successful initialization of the workflow."""
        device_auth_endpoint = faker.url()
        mock_get_sso_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint"
        )
        mock_get_sso_endpoint.return_value = device_auth_endpoint

        mock_device_auth_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.requests.post"
        )
        mock_device_auth_endpoint.return_value.status_code = http.HTTPStatus.OK
        mock_device_auth_endpoint.return_value.json.return_value = (
            lightspeed_auth_response
        )
        auth_request = lightspeed_request_auth()
        assert auth_request == lightspeed_auth_response

    def test_request_with_not_ok_status(self, mocker, lightspeed_auth_response, faker):
        """Test the workflow request resulting in a Not success response."""
        device_auth_endpoint = faker.url()
        mock_get_sso_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint"
        )
        mock_get_sso_endpoint.return_value = device_auth_endpoint

        error_reason = "Endpoint is not implemented."
        mock_device_auth_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.requests.post"
        )
        mock_device_auth_endpoint.return_value.status_code = (
            http.HTTPStatus.NOT_IMPLEMENTED
        )
        mock_device_auth_endpoint.return_value.reason = error_reason
        mock_device_auth_endpoint.return_value.json.return_value = (
            lightspeed_auth_response
        )
        with pytest.raises(LightspeedAuthError) as exception_info:
            _auth_request = lightspeed_request_auth()
        assert messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % error_reason in str(
            exception_info.value
        )

    def test_connection_error(self, mocker, faker):
        """Test for connection error from the device auth endpoint."""
        device_auth_endpoint = faker.url()
        mock_get_sso_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint"
        )
        mock_get_sso_endpoint.return_value = device_auth_endpoint

        err_message = "Cannot connect to the device auth endpoint."
        with mocker.patch(
            "api.auth.auth_lightspeed.requests.post",
            side_effect=ConnectionError(err_message),
        ):
            with pytest.raises(LightspeedAuthError) as exception_info:
                _auth_request = lightspeed_request_auth()
        assert messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % err_message in str(
            exception_info.value
        )

    def test_http_error(self, mocker, faker):
        """Test for a BaseHTTPError from the device auth endpoint."""
        device_auth_endpoint = faker.url()
        mock_get_sso_endpoint = mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint"
        )
        mock_get_sso_endpoint.return_value = device_auth_endpoint

        err_message = "BaseHTTPError to the device auth endpoint."
        with mocker.patch(
            "api.auth.auth_lightspeed.requests.post",
            side_effect=BaseHTTPError(err_message),
        ):
            with pytest.raises(LightspeedAuthError) as exception_info:
                _auth_request = lightspeed_request_auth()
        assert messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % err_message in str(
            exception_info.value
        )


@pytest.mark.django_db
class TestWaitForAuthorization:
    """Test the lightspeed_wait_for_authorization task."""

    def test_invalid_secure_token(self, lightspeed_auth_response, faker):
        """Test that we handle an invalid secure token and do nothing."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]
        return_value = lightspeed_wait_for_authorization(
            faker.pyint(min_value=1001), device_code, interval, expires_in
        )
        assert return_value is None

    def test_connection_error_token_endpoint(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test that ConnectionError from the token endpoint is handled."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        err_message = "Cannot connect to the token endpoint."
        mocker.patch(
            "api.auth.auth_lightspeed.requests.post",
            side_effect=ConnectionError(err_message),
        )
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert (
            metadata["status_reason"]
            == messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % err_message
        )

    def test_http_error_token_endpoint(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test that HTTPError from the token endpoint is handled."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        err_message = "HTTPError while connecting to the token endpoint."
        mocker.patch(
            "api.auth.auth_lightspeed.requests.post",
            side_effect=BaseHTTPError(err_message),
        )
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert (
            metadata["status_reason"]
            == messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % err_message
        )

    def test_successful_token_endpoint_authorization(
        self,
        qpc_user_simple,
        lightspeed_auth_response,
        token_endpoint_response,
        mocker,
        faker,
    ):
        """Test that successful user authorization is handled properly."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = http.HTTPStatus.OK
        mock_token_endpoint.return_value.json.return_value = token_endpoint_response
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert secure_token.token == token_endpoint_response["access_token"]
        assert metadata["status"] == AuthStatus.VALID.value
        assert metadata["status_reason"] == ""

    def test_token_endpoint_authorization_with_invalid_token(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test that a user authorization with an invalid JWT is handled properly."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = http.HTTPStatus.OK
        mock_token_endpoint.return_value.json.return_value = {
            "access_token": "abcdef.ghijkl"
        }
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert metadata["status_reason"] == messages.LIGHTSPEED_INVALID_TOKEN

    def test_token_endpoint_authorization_expired(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test we handle token expiration responses."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = http.HTTPStatus.BAD_REQUEST
        mock_token_endpoint.return_value.json.return_value = {"error": "expired_token"}
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert metadata["status_reason"] == messages.LIGHTSPEED_TOKEN_EXPIRED

    def test_token_endpoint_authorization_unknown_error(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test we handle unknown error for the token endpoint."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        unknown_error = "Unknown error from SSO"
        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = http.HTTPStatus.BAD_REQUEST
        mock_token_endpoint.return_value.reason = unknown_error
        mock_token_endpoint.return_value.json.return_value = {"error": unknown_error}
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert (
            metadata["status_reason"]
            == messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % unknown_error
        )

    def test_token_endpoint_authorization_unhandled_status_code(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test we handle unsupported status codes for the token endpoint."""
        device_code = lightspeed_auth_response["device_code"]
        interval = lightspeed_auth_response["interval"]
        expires_in = lightspeed_auth_response["expires_in"]

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        unprocessable_error = "Unprocessable Entity"
        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = (
            http.HTTPStatus.UNPROCESSABLE_ENTITY
        )
        mock_token_endpoint.return_value.reason = unprocessable_error
        mock_token_endpoint.return_value.json.return_value = {
            "error": unprocessable_error
        }
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert (
            metadata["status_reason"]
            == messages.LIGHTSPEED_LOGIN_VERIFICATION_FAILED % unprocessable_error
        )

    def test_token_endpoint_authorization_handle_timeout(
        self, qpc_user_simple, lightspeed_auth_response, mocker, faker
    ):
        """Test we handle timeout when user did not authorize in time."""
        device_code = lightspeed_auth_response["device_code"]
        interval = 1
        expires_in = 0

        mocker.patch(
            "api.auth.auth_lightspeed.get_sso_endpoint", return_value=faker.url()
        )

        mock_token_endpoint = mocker.patch("api.auth.auth_lightspeed.requests.post")
        mock_token_endpoint.return_value.status_code = http.HTTPStatus.BAD_REQUEST
        mock_token_endpoint.return_value.json.return_value = {
            "error": "authorization_pending"
        }
        secure_token = get_or_create_lightspeed_secure_token(qpc_user_simple)
        lightspeed_wait_for_authorization(
            secure_token.id, device_code, interval, expires_in
        )
        secure_token.refresh_from_db()
        metadata = secure_token.metadata
        assert metadata["status"] == AuthStatus.FAILED.value
        assert (
            metadata["status_reason"] == messages.LIGHTSPEED_LOGIN_VERIFICATION_TIMEOUT
        )
