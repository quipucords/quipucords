"""ansible controller api adapter."""

from logging import getLogger
from math import ceil

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

    def get_paginated_results(self, url, **kwargs):
        """Get a generator with results from a paginated endpoint."""
        # paginated responses on ansible controller api always are always like this
        # { "count": 99, "next": null, "previous": null, "results": [ ... ] }
        kwargs.setdefault("raise_for_status", True)
        first_response = self.get(url, **kwargs)
        first_page = first_response.json()
        yield from first_page["results"]
        if first_page["next"]:
            page_size = len(first_page["results"])
            total_pages = ceil(first_page["count"] / page_size)
            for page in range(2, total_pages + 1):
                params = {"page_size": page_size, "page": page}
                kwargs.setdefault("params", {})
                kwargs["params"].update(**params)
                response = self.get(url, **kwargs)
                yield from response.json()["results"]
