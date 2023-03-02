"""Utility functions for system fingerprinting."""

from collections import OrderedDict

NAME = "name"


def product_entitlement_found(entitlements, product_name):
    """Search entitlements for presences of product_name.

    :param entitlements: list of entitlement dictionaries
    :param product_name: product name to check in entitlements
    :returns: True if found, False otherwise
    """
    if not entitlements:
        return False
    for entitlement in entitlements:
        name = entitlement.get(NAME, "")
        if product_name in name:
            return True
    return False


def strip_prefix(string, prefix):
    """Remove a prefix from a string, if present.

    :param string: the string to operate on.
    :param prefix: the prefix to remove.
    :returns: string without prefix, if prefix was present.
    """
    if string.startswith(prefix):
        return string[len(prefix) :]

    return string


def strip_suffix(string, suffix):
    """Remove a suffix from a string, if present.

    :param string: the string to operate on.
    :param suffix: the suffix to remove.
    :returns: string without suffix, if suffix was present.
    """
    if string.endswith(suffix):
        return string[: -len(suffix)]

    return string


def generate_raw_fact_members(raw_facts_dict):
    """Generate the raw_facts string.

    :param raw_facts_dict: The dictionary of raw_fact names and boolean values
    :returns: string of contributing raw_facts or None
    """
    raw_facts = None
    raw_fact_list = []
    ordered_facts = OrderedDict(sorted(raw_facts_dict.items(), key=lambda t: t[0]))
    for key, value in ordered_facts.items():
        if value:
            raw_fact_list.append(key)
    if raw_fact_list:
        raw_facts = "/".join(raw_fact_list)
    return raw_facts
