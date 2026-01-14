"""RHACS api adapter."""

from logging import getLogger

from requests.auth import AuthBase

from compat.requests import Session
from scanner.utils import format_host_for_url

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

    @staticmethod
    def _format_host_for_url(host: str) -> str:
        """Wrap IPv6 addresses in brackets for proper URL formatting."""
        return format_host_for_url(host)

    @classmethod
    def from_connection_info(  # noqa: PLR0913
        cls,
        *,
        host,
        protocol,
        port,
        auth_token,
        ssl_verify: bool = True,
        proxy_url: str = None,
    ):
        """
        Initialize RHACS session.

        :param host: The host of the server. This can be a hostname or IP address.
        :param protocol: The protocol to use for connecting to the server.
        :param port: The port to use for connecting to the server.
        :param auth_token: The admin token to use for connecting to the server.
        :param ssl_verify: Whether to verify the SSL certificate.
        :param proxy_url: proxy URL in the format 'http(s)://host:port'.
        """
        formatted_host = cls._format_host_for_url(host)
        base_uri = f"{protocol}://{formatted_host}:{port}"
        auth = HTTPBearerAuth(auth_token=auth_token)
        session = cls(base_url=base_uri, verify=ssl_verify, auth=auth)

        if proxy_url:
            session.proxies.update({protocol: proxy_url})
        return session
