"""ansible controller api adapter."""

from concurrent import futures
from copy import deepcopy
from logging import getLogger
from math import ceil

from django.conf import settings
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from compat.requests import Session
from scanner.utils import format_host_for_url

logger = getLogger(__name__)


class AnsibleControllerApi(Session):
    """Specialized Session for ansible controller."""

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
        username=None,
        password=None,
        auth_token=None,
        ssl_verify: bool = True,
        proxy_url: str = None,
    ):
        """
        Initialize AnsibleController session.

        :param host: The host of the server. This can be a hostname or IP address.
        :param protocol: The protocol to use for connecting to the server.
        :param port: The port to use for connecting to the server.
        :param username: The username to use for connecting to the server.
        :param password: The password to use for connecting to the server.
        :param auth_token: Bearer token for OAuth2 authentication.
        :param ssl_verify: Whether to verify the SSL certificate.
        :param proxy_url: proxy URL in the format 'http(s)://host:port'.
        """
        formatted_host = cls._format_host_for_url(host)
        base_uri = f"{protocol}://{formatted_host}:{port}"
        if auth_token:
            session = cls(base_url=base_uri, verify=ssl_verify)
            session.headers["Authorization"] = f"Bearer {auth_token}"
        else:
            auth = HTTPBasicAuth(username=username, password=password)
            session = cls(base_url=base_uri, verify=ssl_verify, auth=auth)

        proxies = {}
        if proxy_url:
            proxies[protocol] = proxy_url

        if proxies:
            session.proxies.update(proxies)
        return session

    def get_paginated_results(self, url, max_concurrency=1, **kwargs):
        """Get a generator with results from a paginated endpoint."""
        # paginated responses on ansible controller api are always like this
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
        total_count = first_page.get("count", 0)
        total_pages = ceil(total_count / page_size) if total_count > 0 else 0
        if total_pages >= settings.QUIPUCORDS_AAP_INSPECT_PAGE_COUNT_FIRST_WARNING:
            logger.warning(
                "AAP server has a large number of result pages (%(total_pages)s "
                "pages for %(total_results)s results). Our client will attempt to "
                "pull all pages, but this may take a while and may add load to the "
                "AAP server.",
                {"total_pages": total_pages, "total_results": total_count},
            )
        for page in range(2, total_pages + 1):
            yield self._format_page_kwargs(kwargs, page_size, page)

    def _format_page_kwargs(self, kwargs, page_size, page):
        kwargs = deepcopy(kwargs)
        params = {"page_size": page_size, "page": page}
        kwargs.setdefault("params", {})
        kwargs["params"].update(**params)
        return kwargs

    def _get_pages_in_parallel(self, url, max_concurrency, page_kwargs):
        logger.info(
            "Fetching %(url)s pages with up to %(max_concurrency)s workers",
            {"url": url, "max_concurrency": max_concurrency},
        )
        if max_concurrency > 10:  # noqa: PLR2004
            # 10 is the default pool size in HTTPAdapter.
            # One might think we could dig through self.adapters["http://"],
            # but the relevant internal configs we need are protected.
            # At this point in execution, we can assume it has the default 10.
            custom_adapter_kwargs = {
                "pool_connections": max_concurrency,
                "pool_maxsize": max_concurrency,
            }
            # It's possible to exhaust the default HTTPAdapter's pool size
            # and hang and pile up connections when we have more threads.
            # So, a "large" max_concurrency means we need to create and mount
            # a new HTTPAdapter that can handle the load.
            # TODO Remove this if we refactor to use Celery tasks instead of threads.
            self.reset_adapters(custom_adapter_kwargs=custom_adapter_kwargs)

        # copy settings to local vars simply to improve readability
        _warn_first = settings.QUIPUCORDS_AAP_INSPECT_PAGE_COUNT_FIRST_WARNING
        _warn_periodic = settings.QUIPUCORDS_AAP_INSPECT_PAGE_COUNT_PERIODIC_WARNING
        executor = futures.ThreadPoolExecutor(max_workers=max_concurrency)
        try:
            future_to_page = {
                executor.submit(self.get, url, **kwargs) for kwargs in page_kwargs
            }
            for count, future_page in enumerate(
                futures.as_completed(future_to_page), start=1
            ):
                if (
                    count >= _warn_first
                    and ((count - _warn_first) % _warn_periodic) == 0
                ):
                    # Warn once at `_warn_first` and then again every `_warn_periodic`.
                    logger.warning(
                        "Processing large number of paginated results from AAP "
                        "server at %(host)s. Current count is %(count)s from %(url)s",
                        {"host": self.base_url, "count": count, "url": url},
                    )

                response = future_page.result()
                if not response.ok:
                    logger.error(
                        "HTTP error %(status)s from %(url)s",
                        {"status": response.status_code, "url": url},
                    )
                    raise response.raise_for_status()
                yield from response.json().get("results", [])
            executor.shutdown(wait=True)
        except HTTPError:
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        except Exception:
            logger.exception(
                "An unexpected error occurred during parallel fetch of %s", url
            )
            executor.shutdown(wait=False, cancel_futures=True)
            raise
