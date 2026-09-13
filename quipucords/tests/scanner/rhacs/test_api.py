"""Test RHACS api client."""

from unittest import mock

import pytest

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
    assert api.proxies == {
        "http": "http://proxy.example.com:8080",
        "https": "http://proxy.example.com:8080",
    }


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

    assert api.proxies == {
        "http": "https://proxy.example.com:8080",
        "https": "https://proxy.example.com:8080",
    }

    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
    assert mock_send.call_count == 1

    prepared_request = mock_send.call_args[0][0]
    assert prepared_request.url == "https://localhost:8080/test"
    assert prepared_request.headers["Authorization"] == "Bearer test_token"


def test_rhacsapi_proxy_survives_http_to_https_redirect(requests_mock):
    """Assert the proxy is still used after the Central route redirects to HTTPS.

    RHACS 4.10 enables automatic HTTP to HTTPS redirection on Central OpenShift
    routes, so a source with SSL disabled is redirected from port 80 to HTTPS.
    requests re-selects the proxy using the redirect target's scheme, so the proxy
    must be registered for HTTPS too. requests keeps the Authorization header on
    its own across this standard port pair.
    """
    api = RHACSApi.from_connection_info(
        host="central.apps.example.com",
        protocol="http",
        port=80,
        auth_token="test_token",
        proxy_url="http://proxy.example.com:8080",
    )
    requests_mock.get(
        "http://central.apps.example.com/v1/auth/status",
        status_code=302,
        headers={"Location": "https://central.apps.example.com/v1/auth/status"},
    )
    requests_mock.get(
        "https://central.apps.example.com/v1/auth/status", json={"userId": "1"}
    )

    response = api.get("/v1/auth/status")

    assert response.status_code == 200
    # Port 80 goes in, but must not come back out: an explicit default port
    # reaches the router as `Host: <host>:80`, and HAProxy's redirect echoes it,
    # sending the HTTPS retry to port 80.
    initial_request = requests_mock.request_history[0]
    assert initial_request.url == "http://central.apps.example.com/v1/auth/status"
    redirected_request = requests_mock.request_history[-1]
    assert redirected_request.url == "https://central.apps.example.com/v1/auth/status"
    assert redirected_request.proxies == {
        "http": "http://proxy.example.com:8080",
        "https": "http://proxy.example.com:8080",
    }
    assert redirected_request.headers["Authorization"] == "Bearer test_token"


@pytest.mark.parametrize(
    "protocol,port,expected",
    (
        ("http", 80, "http://central.apps.example.com"),
        ("https", 443, "https://central.apps.example.com"),
        ("http", 8080, "http://central.apps.example.com:8080"),
        ("https", 8443, "https://central.apps.example.com:8443"),
    ),
)
def test_rhacsapi_omits_default_port_from_base_url(protocol, port, expected):
    """Assert a port that is the scheme default is left out of the base URL.

    An explicit default port reaches the server as `Host: <host>:80`, and
    HAProxy's `redirect scheme https` reuses that header verbatim. The Central
    route would then redirect to `https://<host>:80`, whose TLS handshake hits
    the router's plaintext listener and dies with WRONG_VERSION_NUMBER.
    """
    api = RHACSApi.from_connection_info(
        host="central.apps.example.com",
        protocol=protocol,
        port=port,
        auth_token="test_token",
    )

    assert api.base_url == expected


def test_rhacsapi_instantiation_with_ipv6_host():
    """Assert IPv6 hosts are properly formatted in the URL."""
    api = RHACSApi.from_connection_info(
        host="fd00:dead:beef::126",
        protocol="https",
        port=6443,
        auth_token="test_token",
    )

    assert api.base_url == "https://[fd00:dead:beef::126]:6443"
