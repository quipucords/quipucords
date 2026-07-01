"""Test compat.requests module."""

import httpretty
import pytest
from requests import Session as RequestsSession

from compat.requests import Session


@pytest.mark.parametrize(
    "extra_kwargs,expected_kwargs",
    (
        # requests>=2.34.2 explicitly passes params=None from get() to request()
        ({}, {"params": None, "allow_redirects": True}),
        ({"allow_redirects": False}, {"params": None, "allow_redirects": False}),
        ({"foo": "bar"}, {"params": None, "allow_redirects": True, "foo": "bar"}),
    ),
)
def test_base_url_injection(mocker, extra_kwargs, expected_kwargs):
    """Test base_url injection in requests.Session."""
    mocked_session_request = mocker.patch.object(RequestsSession, "request")
    session = Session(base_url="http://some.url")
    session.get("/api/endpoint/", **extra_kwargs)
    mocked_session_request.assert_called_once()
    args, kwargs = mocked_session_request.call_args
    assert args == ("GET", "http://some.url/api/endpoint/")
    for key, value in expected_kwargs.items():
        assert kwargs[key] == value


@httpretty.activate
def test_automatic_retry():
    """Test automatic retry on select status codes."""
    httpretty.register_uri(
        httpretty.GET,
        "http://some.url/",
        responses=[
            httpretty.Response("TOO MANY REQUESTS", status=429),
            httpretty.Response('{"message": "ok"}'),
        ],
    )
    # lets compare our custom session with requests default
    requests_session = RequestsSession()
    req_response = requests_session.get("http://some.url/")
    assert req_response.status_code >= 400
    # now our custom session
    session = Session()
    qpc_resp = session.get("http://some.url/")
    assert qpc_resp.ok
    assert qpc_resp.json() == {"message": "ok"}
