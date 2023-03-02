"""Status misc module."""

from functools import cache

from .model import ServerInformation


@cache
def get_server_id():
    """Get server_id and cache it."""
    return ServerInformation.create_or_retrieve_server_id()
