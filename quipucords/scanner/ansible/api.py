"""ansible controller api adapter."""

from logging import getLogger

from requests.auth import HTTPBasicAuth

from compat.requests import Session

logger = getLogger(__name__)


class AnsibleControllerApi(Session):
    """Specialized Session for ansible controller."""

    @classmethod
    def from_connection_info(
        cls, *, host, protocol, port, username, password, ssl_verify: bool = True
    ):
        """
        Initialize AnsibleController session.

        :param host: The host of the server. This can be a hostname or IP address.
        :param protocol: The protocol to use for connecting to the server.
        :param port: The port to use for connecting to the server.
        :param username: The username to use for connecting to the server.
        :param password: The password to use for connecting to the server.
        :param ssl_verify: Whether to verify the SSL certificate.
        """
        base_uri = f"{protocol}://{host}:{port}"
        auth = HTTPBasicAuth(username=username, password=password)
        return cls(base_url=base_uri, verify=ssl_verify, auth=auth)
