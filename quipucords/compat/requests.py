"""quipucords/requests compat/utility adapters."""

from urllib.parse import urljoin

import requests
from django.conf import settings
from urllib3 import Retry


class Session(requests.Session):
    """
    Specialized request session with a configurable base_url.

    This class also has some usability enhancements, like commonly attributes we'd set
    for each session available in its initialization.
    """

    DEFAULT_STATUS_CODE_LIST_FOR_RETRY = [429, 500, 502, 503]

    def __init__(  # noqa: PLR0913
        self,
        *,
        base_url=None,
        auth=None,
        verify=True,
        max_retries=None,
        backoff_factor=None,
        retry_on_status_code_list=None,
    ):
        """
        Initialize the class.

        :param base_url: The base URL for the API
        :param auth: Auth class (as specified on requests documentation [1])
        :param verify: SSL verify
        :param max_retries: maximum number of automatic retries
        :param backoff_factor: backoff factor for automatic retries
        :param retry_on_status_code_list: list of status codes eligible for automatic
            retry. Defaults to DEFAULT_STATUS_CODE_LIST_FOR_RETRY`

        [1]: https://requests.readthedocs.io/en/latest/user/authentication/#authentication
        """  # noqa: E501
        super().__init__()
        self.verify = verify
        self.base_url = base_url
        self.auth = auth
        self._max_retries = (
            settings.QUIPUCORDS_HTTP_RETRY_MAX_NUMBER
            if max_retries is None
            else max_retries
        )
        if self._max_retries > 0:
            self._backoff_factor = (
                backoff_factor or settings.QUIPUCORDS_HTTP_RETRY_BACKOFF
            )
            self._retry_on_status_code_list = (
                retry_on_status_code_list or self.DEFAULT_STATUS_CODE_LIST_FOR_RETRY
            )
            self.reset_adapters()
        else:
            self._backoff_factor = None
            self._retry_on_status_code_list = []

    def reset_adapters(
        self,
        *,
        custom_retry_kwargs: dict | None = None,
        custom_adapter_kwargs: dict | None = None,
    ):
        """Mount new HTTPAdapter with optionally overridden kwargs."""
        retry_kwargs = {
            "total": self._max_retries,
            "status_forcelist": self._retry_on_status_code_list,
            "backoff_factor": self._backoff_factor,
        }
        if custom_retry_kwargs:
            retry_kwargs.update(custom_retry_kwargs)

        adapter_kwargs = {"max_retries": Retry(**retry_kwargs)}
        if custom_adapter_kwargs:
            adapter_kwargs.update(custom_adapter_kwargs)

        adapter = requests.adapters.HTTPAdapter(**adapter_kwargs)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def request(
        self, method, url, *, raise_for_status=False, **kwargs
    ) -> requests.Response:
        """
        Prepare and send a request.

        This is a wrapper around :meth: `requests.Session.request`

        :param method: The HTTP method to use
        :param url: The URL to send the request to. This can be relative to the base URL
        :param raise_for_status: (optional) call Response method "raise_for_status".
        :param **kwargs: same keyword arguments used on parent class request method.
        :returns: `requests.Response`
        """
        request_url = urljoin(self.base_url, url)
        response = super().request(method, request_url, **kwargs)
        if raise_for_status:
            response.raise_for_status()
        return response
