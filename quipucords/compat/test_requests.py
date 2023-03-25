"""Test compat.requests module."""

import pytest
from requests import Session as RequestsSession

from compat.requests import Session


@pytest.mark.parametrize(
    "extra_kwargs,expected_kwargs",
    (
        ({}, {"allow_redirects": True}),
        ({"allow_redirects": False}, {"allow_redirects": False}),
        ({"foo": "bar"}, {"allow_redirects": True, "foo": "bar"}),
    ),
)
def test_base_url_injection(mocker, extra_kwargs, expected_kwargs):
    """Test base_url injection in requests.Session."""
    mocked_session_request = mocker.patch.object(RequestsSession, "request")
    session = Session(base_url="http://some.url")
    session.get("/api/endpoint/", **extra_kwargs)
    assert mocked_session_request.mock_calls == [
        mocker.call(
            "GET",
            "http://some.url/api/endpoint/",
            **expected_kwargs,
        )
    ]
