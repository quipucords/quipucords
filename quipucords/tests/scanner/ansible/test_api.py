"""Test ansible controller api client."""

import json
import logging
import math
from unittest import mock

import httpretty
import pytest
from django.test import override_settings
from requests.auth import HTTPBasicAuth
from requests.exceptions import RetryError
from urllib3.exceptions import MaxRetryError, ResponseError

from scanner.ansible.api import AnsibleControllerApi


@pytest.fixture
def paginated_results(request):
    """Simulate a paginated result."""
    count, page_size, failures = request.param
    if failures is None:
        # By default, produce a failure on page 2's 0th (first) attempt
        failures = {2: [0]}

    httpretty.enable()

    max_page = math.ceil(count / page_size) if page_size > 0 else 0
    for page in range(1, max_page + 1):
        failure_on_attempts = failures.get(page, [])
        success_response_body = json.dumps(
            {
                "count": count,
                "next": count > (page * page_size),
                "results": list(
                    range((page - 1) * page_size + 1, min(count, page * page_size) + 1)
                ),  # generate simple list of numbers to represent result objects
            }
        )

        responses = []
        for attempt in range(len(failure_on_attempts) + 1):
            # +1 allows the client to call again to get a success after the failure
            if attempt in failure_on_attempts:
                responses.append(
                    httpretty.Response("Service temporarily unavailable", status=503)
                )
            else:
                responses.append(httpretty.Response(success_response_body, status=200))

        httpretty.register_uri(
            httpretty.GET,
            f"https://some.url/paginated/?&page={page}&page_size={page_size}",
            match_querystring=True,
            responses=responses,
        )

        if page == 1:
            # Special case "no args" handling for only the first page.
            httpretty.register_uri(
                httpretty.GET,
                "https://some.url/paginated/",
                match_querystring=True,
                body=success_response_body,
            )
    yield
    httpretty.disable()


@pytest.mark.parametrize("paginated_results", [[11, 5, None]], indirect=True)
def test_get_paginated_results(paginated_results, caplog):
    """Test get_paginated_results method."""
    caplog.set_level(logging.WARNING)
    client = AnsibleControllerApi(base_url="https://some.url/")
    results = client.get_paginated_results("/paginated/", max_concurrency=4)
    assert set(results) == set(range(1, 12))
    assert len(caplog.messages) == 0
    # WARNING: the next two lines are potentially brittle and may need to be removed.
    assert client.adapters["http://"]._pool_connections == 10  # default value
    assert client.adapters["http://"]._pool_maxsize == 10  # default value


@override_settings(QUIPUCORDS_AAP_INSPECT_PAGE_COUNT_FIRST_WARNING=10)
@override_settings(QUIPUCORDS_AAP_INSPECT_PAGE_COUNT_PERIODIC_WARNING=3)
@pytest.mark.parametrize("paginated_results", [[100, 5, dict()]], indirect=True)
def test_get_paginated_results_logs_warnings(paginated_results, caplog):
    """
    Test get_paginated_results logs warnings at large page counts.

    With the given parameters, we expect:
    * fake API has 100 results over 20 pages (page size 5).
    * fake API will never return an error.
    * request for first page will emit a general warning about expecting many pages.
    * request for page 10 will emit a page-specific "large" warning.
    * request for pages 13, 16, and 19 will also emit "large" warnings.
    """
    caplog.set_level(logging.WARNING)
    client = AnsibleControllerApi(base_url="https://some.url/")
    results = client.get_paginated_results("/paginated/", max_concurrency=4)
    assert set(results) == set(range(1, 101))
    assert len(caplog.messages) == 5
    assert "20 pages for 100 results" in caplog.records[0].message
    messages = sorted(caplog.messages[1:])  # in case concurrency generated out of order
    expected_periodic_count_warnings = [10, 13, 16, 19]
    for message, expected_count in zip(messages, expected_periodic_count_warnings):
        assert f"Current count is {expected_count}" in message


@pytest.mark.parametrize("paginated_results", [[200, 5, dict()]], indirect=True)
def test_get_paginated_results_big_max_concurrency(paginated_results, caplog):
    """Test get_paginated_results works with large max_concurrency."""
    caplog.set_level(logging.ERROR)
    client = AnsibleControllerApi(base_url="https://some.url/")
    results = client.get_paginated_results("/paginated/", max_concurrency=30)
    assert set(results) == set(range(1, 201))
    assert len(caplog.messages) == 0
    # WARNING: the next two lines are potentially brittle and may need to be removed.
    assert client.adapters["http://"]._pool_connections == 30
    assert client.adapters["http://"]._pool_maxsize == 30


@pytest.mark.parametrize(
    "paginated_results",
    [[200, 5, dict({2: range(10), 3: range(10), 4: range(10)})]],
    indirect=True,
)
def test_get_paginated_results_many_errors(paginated_results, caplog):
    """Test get_paginated_results raises exception after too many HTTP errors."""
    caplog.set_level(logging.ERROR)
    client = AnsibleControllerApi(base_url="https://some.url/")
    client._backoff_factor = 0.001  # massively speed up retries after failures
    client.reset_adapters()  # force client to use that custom backoff
    results = []
    with pytest.raises((MaxRetryError, ResponseError, RetryError)):
        for result in client.get_paginated_results("/paginated/", max_concurrency=2):
            results.append(result)
    # Some results MAY have been generated, but it should be less than total expected.
    assert len(results) < 200


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


def test_ansible_api_instantiation_with_ipv6_host():
    """Assert IPv6 hosts are properly formatted in the URL."""
    api = AnsibleControllerApi.from_connection_info(
        host="fd00:dead:beef::126",
        protocol="https",
        port=6443,
        username="test_username",
        password="test_password",
    )

    assert api.base_url == "https://[fd00:dead:beef::126]:6443"


def test_ansible_api_instantiation_with_auth_token():
    """Assert bearer token auth sets Authorization header without HTTPBasicAuth."""
    api = AnsibleControllerApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8443,
        auth_token="my-bearer-token",
        ssl_verify=True,
    )

    assert api.base_url == "https://localhost:8443"
    assert api.headers["Authorization"] == "Bearer my-bearer-token"
    assert api.auth is None


def test_ansible_api_instantiation_with_user_pass_no_bearer():
    """Assert username/password uses HTTPBasicAuth and no bearer header."""
    api = AnsibleControllerApi.from_connection_info(
        host="localhost",
        protocol="https",
        port=8443,
        username="admin",
        password="secret",
    )

    assert isinstance(api.auth, HTTPBasicAuth)
    assert "Authorization" not in api.headers
