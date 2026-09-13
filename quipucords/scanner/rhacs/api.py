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

    DEFAULT_PORTS = {"http": 80, "https": 443}

    @staticmethod
    def _format_host_for_url(host: str) -> str:
        """Wrap IPv6 addresses in brackets for proper URL formatting."""
        return format_host_for_url(host)

    @classmethod
    def _build_netloc(cls, host: str, protocol: str, port) -> str:
        """Join host and port, omitting the port when it is the scheme default.

        An explicit default port ends up in the Host header, and HAProxy's
        `redirect scheme https` reuses that header verbatim. A source on port 80
        would therefore be redirected to `https://<host>:80`, where the TLS
        handshake hits the plaintext listener and fails with WRONG_VERSION_NUMBER.
        """
        formatted_host = cls._format_host_for_url(host)
        if port is None or int(port) == cls.DEFAULT_PORTS.get(protocol):
            return formatted_host
        return f"{formatted_host}:{port}"

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
        base_uri = f"{protocol}://{cls._build_netloc(host, protocol, port)}"
        auth = HTTPBearerAuth(auth_token=auth_token)
        session = cls(base_url=base_uri, verify=ssl_verify, auth=auth)

        if proxy_url:
            # Register the proxy for both schemes. RHACS 4.10 redirects Central
            # OpenShift routes from HTTP to HTTPS, and requests re-selects the proxy
            # using the redirect target's scheme. Registering only the source's own
            # scheme would silently bypass the proxy after the redirect.
            session.proxies.update({"http": proxy_url, "https": proxy_url})
        return session
