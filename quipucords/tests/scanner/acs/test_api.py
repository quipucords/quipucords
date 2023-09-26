"""Test ACS api client."""

from unittest import mock

from scanner.acs.api import ACSApi, HTTPBearerAuth


def test_http_bearer_auth():
    """Test HTTPBearerAuth call function."""
    auth_token = "sample_token"
    auth = HTTPBearerAuth(auth_token)

    mock_request_instance = mock.Mock()
    mock_request_instance.headers = {}

    modified_request = auth(mock_request_instance)
    assert "Authorization" in modified_request.headers
    assert modified_request.headers["Authorization"] == "Bearer " + auth_token


def test_acsapi_instantiation_with_connection_info():
    """Assert an instance of ACSApi is being created correctly."""
    api = ACSApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8080,
        auth_token="YOUR_AUTH_TOKEN",
    )

    # Assert that the session is initialized correctly.
    assert api.base_url == "https://localhost:8080"
    assert api.auth.auth_token == "YOUR_AUTH_TOKEN"
    assert isinstance(api.auth, HTTPBearerAuth)
