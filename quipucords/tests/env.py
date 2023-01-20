"""
env module.

Utilities for handling env vars in testing.
"""
import os
from functools import cached_property
from urllib.parse import urlparse, urlunparse


class EnvVar:
    """
    Environment value with an fallback value.

    The environment variable name will match the name of the attribute
    where this is instantiated.
    """

    def __init__(self, fallback_value, coercer=str):
        """Initialize EnvVar."""
        self.coercer = coercer
        self._fallback_value = fallback_value
        # env_var will be set when EnvVar becomes an attribute of another class
        self.env_var = None

    @cached_property
    def value(self):
        """Return the value from envvar (or fallback value)."""
        assert self.env_var
        val_from_env = os.environ.get(self.env_var)
        if val_from_env is None:
            return self.fallback_value
        return self.coercer(val_from_env)

    @cached_property
    def fallback_value(self):
        """Return the fallback value."""
        return self.coercer(self._fallback_value)

    def __set_name__(self, obj, name):
        """Set env var name."""
        self.env_var = name
        # coerce value/fallback value to validate'em
        self.value and self.fallback_value  # pylint: disable=pointless-statement

    def __str__(self):
        """Return str representation."""
        return self.value


class BaseURI:
    """
    BaseURI class.

    BaseURI represents the three initial parts on an URI: protocol/scheme, host
    and port.
    """

    def __init__(self, base_uri: str):
        """Initialize BaseURI."""
        self._uri = base_uri
        self.parsed_uri = self.urlparse(self._uri)

    def __eq__(self, other):
        """Compare BaseURI with other object."""
        return self._uri == other

    def __str__(self) -> str:
        """Return BaseURI str representation."""
        return self._uri

    def __hash__(self):
        """Return BaseURI hash value."""
        return hash(self._uri)

    @property
    def protocol(self):
        """Return BaseURI protocol."""
        return self.parsed_uri.scheme

    @property
    def host(self):
        """Return BaseURI host."""
        return self.parsed_uri.hostname

    @property
    def port(self):
        """Return BaseURI port."""
        return self.get_port(self.parsed_uri)

    @classmethod
    def get_port(cls, parsed_uri):
        """Return port from the return of urlparse function."""
        _port = parsed_uri.port
        if _port is None:
            return {"https": 443, "http": 80}[parsed_uri.scheme]
        return _port

    @classmethod
    def urlparse(cls, base_uri: str):
        """Parse a string representing a BaseURI."""
        parsed_uri = urlparse(base_uri)
        protocol, host, *other_parts = parsed_uri  # pylint: disable=unused-variable
        if other_parts != [""] * 4:
            raise ValueError(
                f"BaseURI ({base_uri}) should contain only schema, hostname and port"
            )
        return parsed_uri

    def replace_base_uri(self, uri: str):
        """Replace protocol, host and port from an uri with this instance values."""
        protocol, host, *other_parts = urlparse(uri)  # pylint: disable=unused-variable
        return urlunparse((self.protocol, f"{self.host}:{self.port}", *other_parts))


def as_bool(value) -> bool:
    """Coerce an environment variable value as boolean."""
    if value.strip().lower() in ["0", "false", ""]:
        return False
    return True
