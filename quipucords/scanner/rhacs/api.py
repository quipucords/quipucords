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
        cls,
        *,
        host,
        protocol,
        port,
        auth_token,
        ssl_verify: bool = True,
        http_proxy: str = None,
        https_proxy: str = None,
    ):
        """
        Initialize RHACS session.

        :param host: The host of the server. This can be a hostname or IP address.
        :param protocol: The protocol to use for connecting to the server.
        :param port: The port to use for connecting to the server.
        :param auth_token: The admin token to use for connecting to the server.
        :param ssl_verify: Whether to verify the SSL certificate.
        :param http_proxy: Optional HTTP proxy in the format "host:port".
        :param https_proxy: Optional HTTPS proxy in the format "host:port".
        """
        base_uri = f"{protocol}://{host}:{port}"
        auth = HTTPBearerAuth(auth_token=auth_token)
        session = cls(base_url=base_uri, verify=ssl_verify, auth=auth)

        proxies = {}
        if http_proxy:
            proxies["http"] = "http://" + http_proxy
        if https_proxy:
            proxies["https"] = "http://" + https_proxy

        if proxies:
            session.proxies.update(proxies)
        return session
