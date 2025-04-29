"""Test RHACS api client."""

from unittest import mock

from scanner.rhacs.api import HTTPBearerAuth, RHACSApi


def test_http_bearer_auth():
    """Test HTTPBearerAuth call function."""
    auth_token = "sample_token"
    auth = HTTPBearerAuth(auth_token)

    mock_request_instance = mock.Mock()
    mock_request_instance.headers = {}

    modified_request = auth(mock_request_instance)
    assert "Authorization" in modified_request.headers
    assert modified_request.headers["Authorization"] == "Bearer " + auth_token


def test_rhacsapi_instantiation_with_connection_info():
    """Assert an instance of RHACSApi is created correctly with proxy."""
    api = RHACSApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8443,
        auth_token="test_token",
        ssl_verify=False,
        proxy_url="http://proxy.example.com:8080",
    )

    assert api.base_url == "https://localhost:8443"
    assert api.auth.auth_token == "test_token"
    assert isinstance(api.auth, HTTPBearerAuth)
    assert api.verify is False
    assert api.proxies == {"https": "http://proxy.example.com:8080"}


@mock.patch("requests.Session.send")
def test_rhacsapi_api_call_uses_proxy(mock_send):
    """Ensure an API call is sent through the configured proxy."""
    api = RHACSApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8080,
        auth_token="test_token",
        proxy_url="https://proxy.example.com:8080",
    )
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "ok"}
    mock_send.return_value = mock_response

    response = api.get("/test")

    assert api.proxies == {"https": "https://proxy.example.com:8080"}

    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
    assert mock_send.call_count == 1

    prepared_request = mock_send.call_args[0][0]
    assert prepared_request.url == "https://localhost:8080/test"
    assert prepared_request.headers["Authorization"] == "Bearer test_token"
