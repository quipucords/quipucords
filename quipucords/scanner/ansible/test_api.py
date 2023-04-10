"""Test ansible controller api client."""

import httpretty
import pytest

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
