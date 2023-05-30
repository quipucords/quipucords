"""ansible controller api adapter."""

from concurrent import futures
from copy import deepcopy
from logging import getLogger
from math import ceil

from requests.auth import HTTPBasicAuth

from compat.requests import Session

logger = getLogger(__name__)


class AnsibleControllerApi(Session):
    """Specialized Session for ansible controller."""

    @classmethod
    def from_connection_info(  # noqa: PLR0913
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

    def get_paginated_results(self, url, max_concurrency=1, **kwargs):
        """Get a generator with results from a paginated endpoint."""
        # paginated responses on ansible controller api always are always like this
        # { "count": 99, "next": null, "previous": null, "results": [ ... ] }
        kwargs.setdefault("raise_for_status", True)
        first_response = self.get(url, **kwargs)
        first_page = first_response.json()
        yield from first_page["results"]
        if first_page["next"]:
            page_kwargs = self._get_page_params(kwargs, first_page)
            yield from self._get_pages_in_parallel(url, max_concurrency, page_kwargs)

    def _get_page_params(self, kwargs, first_page):
        page_size = len(first_page["results"])
        total_pages = ceil(first_page["count"] / page_size)
        for page in range(2, total_pages + 1):
            yield self._format_page_kwargs(kwargs, page_size, page)

    def _format_page_kwargs(self, kwargs, page_size, page):
        kwargs = deepcopy(kwargs)
        params = {"page_size": page_size, "page": page}
        kwargs.setdefault("params", {})
        kwargs["params"].update(**params)
        return kwargs

    def _get_pages_in_parallel(self, url, max_concurrency, page_kwargs):
        with futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            future_to_page = {
                executor.submit(self.get, url, **kwargs) for kwargs in page_kwargs
            }
            for future_page in futures.as_completed(future_to_page):
                data = future_page.result()
                yield from data.json()["results"]
