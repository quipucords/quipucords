"""Module for default_getter function."""

from typing import Any, Hashable


def default_getter(data: dict, key: Hashable, default_value: Any) -> Any:
    """Get value from dict with a default value if it does not exist or is None."""
    val = data.get(key, default_value)
    if val is None:
        return default_value
    return val
