"""RHACS api adapter."""

from logging import getLogger

from requests.auth import AuthBase

from compat.requests import Session

logger = getLogger(__name__)


class HTTPBearerAuth(AuthBase):
    """A class for implementing HTTP Bearer Token Authentication."""

    def __init__(self, auth_token):
        self.auth_token = auth_token

    def __call__(self, r):
        """Add the Bearer token to the headers and return the modified request."""
        r.headers["Authorization"] = "Bearer " + self.auth_token
        return r


class RHACSApi(Session):
    """Specialized Session for RHACS."""

    @classmethod
    def from_connection_info(  # noqa: PLR0913
        cls, *, host, protocol, port, auth_token, ssl_verify: bool = True
    ):
        """
        Initialize RHACS session.

        :param host: The host of the server. This can be a hostname or IP address.
        :param protocol: The protocol to use for connecting to the server.
        :param port: The port to use for connecting to the server.
        :param auth_token: The admin token to use for connecting to the server.
        :param ssl_verify: Whether to verify the SSL certificate.
        """
        base_uri = f"{protocol}://{host}:{port}"
        auth = HTTPBearerAuth(auth_token=auth_token)
        return cls(base_url=base_uri, verify=ssl_verify, auth=auth)
