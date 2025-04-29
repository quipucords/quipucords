"""Test ansible controller api client."""

from unittest import mock

import httpretty
import pytest
from requests.auth import HTTPBasicAuth

from scanner.ansible.api import AnsibleControllerApi


@pytest.fixture
def paginated_results():
    """Simulate a paginated result."""
    httpretty.enable()

    httpretty.register_uri(
        httpretty.GET,
        "https://some.url/paginated/",
        match_querystring=True,
        body='{"count": 11, "next": true, "results": [1, 2, 3, 4, 5]}',
    )
    httpretty.register_uri(
        httpretty.GET,
        "https://some.url/paginated/?&page=2&page_size=5",
        match_querystring=True,
        responses=[
            httpretty.Response("Service temporarily unavailable", status=503),
            httpretty.Response(
                '{"count": 11, "next": true, "results": [6, 7, 8, 9, 10]}', status=200
            ),
        ],
    )

    httpretty.register_uri(
        httpretty.GET,
        "https://some.url/paginated/?&page=3&page_size=5",
        body='{"count": 11, "next": false, "results": [11]}',
        match_querystring=True,
    )
    yield
    httpretty.disable()


def test_get_paginated_results(paginated_results):
    """Test get_paginated_results method."""
    client = AnsibleControllerApi(base_url="https://some.url/")
    results = client.get_paginated_results("/paginated/", max_concurrency=4)
    assert set(results) == set(range(1, 12))


def test_ansible_api_instantiation_with_connection_info():
    """Assert an instance of AnsibleControllerApi is created correctly with proxy."""
    api = AnsibleControllerApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8443,
        username="test_username",
        password="test_password",
        ssl_verify=False,
        proxy_url="http://proxy.example.com:8080",
    )

    assert api.base_url == "https://localhost:8443"
    assert api.auth.username == "test_username"
    assert isinstance(api.auth, HTTPBasicAuth)
    assert api.verify is False
    assert api.proxies == {"https": "http://proxy.example.com:8080"}


@mock.patch("requests.Session.send")
def test_ansible_api_call_uses_proxy(mock_send):
    """Ensure an API call is sent through the configured proxy."""
    api = AnsibleControllerApi.from_connection_info(
        host="localhost",
        protocol="http",
        port=8080,
        username="test_username",
        password="test_password",
        proxy_url="https://proxy.example.com:8080",
    )
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "ok"}
    mock_send.return_value = mock_response

    response = api.get("/test")

    assert api.proxies == {"http": "https://proxy.example.com:8080"}

    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
    assert mock_send.call_count == 1

    prepared_request = mock_send.call_args[0][0]
    assert prepared_request.url == "http://localhost:8080/test"
