"""Flow server version to clients."""

from quipucords.environment import server_version


class ServerVersionMiddle:
    """Middleware class to flow server version to clients."""

    # pylint: disable=too-few-public-methods
    def __init__(self, get_response):
        """Initialize middleware class."""
        self.get_response = get_response

    def __call__(self, request):
        """Add server version header to response."""
        response = self.get_response(request)
        response["X-Server-Version"] = server_version()
        return response
