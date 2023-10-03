"""Helpers to handle facts."""

import random
import string


def fact_expander(fact_name):
    """Expand a fact name to cover all "parent" facts."""
    vals = set(fact_name.split("/"))
    return {fact.split("__")[0] for fact in vals}


def random_name(min_length=5, max_length=15):
    """Generate a random string."""
    characters = string.ascii_letters + string.digits + "-."
    return "".join(random.choices(characters, k=random.randint(min_length, max_length)))


def random_value():
    """Generate a random value."""
    values = [["foo", "bar"], {"foo": "bar"}, 42, None, True, "foo", 3.14]
    return random.choice(values)


class RawFactComparator:
    """
    Comparator for raw facts.

    If the expanded fact A has an intersection with the expanded fact B, then
    this comparator consider they are equal.
    See `fact_expander` and `__eq__` implementation for more details.

    This comparator supports:
    - simple fact notation (i.e. "fact_name")
    - ambigous fact notation (i.e. "fact_name/other_fact_name")
    - parent from nested facts (i.e. "fact_name__some_nested_key")

    Note:
    Distinct "child" facts coming from the same "parent" (i.e.
    "system_purpose_json__addons" and "system_purpose_json__usage") are considered
    equal as they are comming from the fact.
    """

    def __init__(self, fact_name):
        """Initialize class."""
        self._fact = fact_name
        self._vals = fact_expander(self._fact)

    def __eq__(self, other):
        """Operator for ==."""
        if isinstance(other, str):
            return self.__class__(other) == self._vals
        if isinstance(other, set):
            return other & self._vals != set()
        if isinstance(other, self.__class__):
            return other._vals == self
        raise TypeError(
            f"'{other}' is unsupported comparison with facts "
            f"(type={type(other).__name__})"
        )

    def __str__(self):
        """Dunder str."""
        return self._fact

    def __repr__(self):
        """Dunder repr."""
        return f"<{self.__class__.__name__} {self._fact}>"
