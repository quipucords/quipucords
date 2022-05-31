# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Http utils for quipucords testing."""
# pylint: disable=unused-import
from functools import cached_property
from urllib.parse import urljoin

import requests


class BaseUrlClient(requests.Session):
    """Specialized request session with a configurable base_url."""

    def __init__(self, *, base_url=None, auth=None, verify=False, **kwargs):
        """
        Initialize ApiClient.

        base_url: will be prepended to all requests urls
        auth: Auth class (as specified on requests documentation)
        verify: SSL verify (default set to False)
        """
        super().__init__(**kwargs)
        self.verify = verify
        self.base_url = base_url
        self.auth = auth

    def request(self, method, url, *args, **kwargs):
        """Prepare a request and send it."""
        request_url = urljoin(self.base_url, url)
        return super().request(method, request_url, *args, **kwargs)


class QPCAuth(requests.auth.AuthBase):
    """Auth class for Quipucords server."""

    def __init__(self, *, base_url, username, password):
        """Initialize QPCAuth."""
        self._qpc_client = BaseUrlClient(base_url=base_url)
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
