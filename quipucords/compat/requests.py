"""quipucords/requests compat/utility adapters."""

from urllib.parse import urljoin

import requests


class Session(requests.Session):
    """
    Specialized request session with a configurable base_url.

    This class also has some usability enhancements, like commonly attributes we'd set
    for each session available in its initialization.
    """

    def __init__(self, *, base_url=None, auth=None, verify=True):
        """
        Initialize the class.

        :param base_url: The base URL for the API
        :param auth: Auth class (as specified on requests documentation [1])
        :param verify: SSL verify

        [1]: https://requests.readthedocs.io/en/latest/user/authentication/#authentication
        """  # noqa: E501
        super().__init__()
        self.verify = verify
        self.base_url = base_url
        self.auth = auth

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        """
        Prepare amd send a request.

        This is a wrapper around :meth: `requests.Session.request`

        :param method: The HTTP method to use
        :param url: The URL to send the request to. This can be relative to the base URL
        :returns: `requests.Response`
        """
        request_url = urljoin(self.base_url, url)
        return super().request(method, request_url, *args, **kwargs)
