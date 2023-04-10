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

    def request(  # pylint: disable=arguments-differ
        self, method, url, *, raise_for_status=False, **kwargs
    ) -> requests.Response:
        """
        Prepare amd send a request.

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
