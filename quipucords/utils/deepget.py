# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Module for deepget function."""


def _get_item(data, key):
    """
    Get value mapped/indexed to key on data.

    Will always return None if key is not found.
    """
    try:
        return data[key]
    except TypeError:
        try:
            # trying to coerce key to int - assuming data is a list-like object
            key = int(key)
        except ValueError:
            return None
        return _get_item(data, key)
    except (IndexError, KeyError):
        return None


def _get_nested_item(data, *keys):
    if len(keys) == 1:
        # last element - just grab it and return it
        current_key = keys[0]
        return _get_item(data, current_key)

    current_key, *next_keys = keys
    # get element for the leftmost key
    item = _get_item(data, current_key)
    if getattr(item, "__getitem__", None) and not isinstance(item, str):
        return _get_nested_item(item, *next_keys)
    # item is not dict/list-like - end recursion
    return None


def deepget(data, path):
    """
    Get data nested inside a dictionary and or list that came from a json.

    To get a nested data use __ as a "lookup" separator.
    If the data can't be found, `None` is returned.

    Example usage
    =============
    >>> data = {"foo": {"bar": "bla", "some_list": ["foo", "bar"]}}
    >>> assert deepget(data, "foo__bar") == "bla"
    >>> assert deepget(data, "foo__bar__some_list__0") == "foo"

    Notes and limitations
    =====================
    - Keys containing "__" will be ignored
    - Dict-like objects: only strings are supported as keys (since this function was
      designed to access data parsed from json)
    - List-like objects: indexes are expected to be integers
    - set: sets are unsupported
    """
    try:
        keys = path.split("__")
    except AttributeError as error:
        raise ValueError(f"{path=} should be a string, not {type(path)}.") from error
    return _get_nested_item(data, *keys)
