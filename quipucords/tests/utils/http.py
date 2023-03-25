"""Http utils for quipucords testing."""

from functools import cached_property

import requests

from compat.requests import Session


class QPCAuth(requests.auth.AuthBase):
    """Auth class for Quipucords server."""

    def __init__(self, *, base_url, username, password, **kwargs):
        """Initialize QPCAuth."""
        self._qpc_client = Session(base_url=base_url, **kwargs)
        self._username = username
        self._password = password

    def __call__(self, r: requests.PreparedRequest):
        """Add authorization token to request headers."""
        r.headers["Authorization"] = f"Token {self.auth_token}"
        return r

    @cached_property
    def auth_token(self):
        """QPC auth token."""
        auth_response = self._qpc_client.post(
            "api/v1/token/", {"username": self._username, "password": self._password}
        )
        assert auth_response.ok, auth_response.text
        return auth_response.json()["token"]
