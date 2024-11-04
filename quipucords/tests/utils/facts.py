"""Helpers to handle facts."""


def fact_expander(fact_name):
    """Expand a fact name to cover all "parent" facts."""
    vals = set(fact_name.split("/"))
    return {fact.split("__")[0] for fact in vals}


class RawFactComparator:
    """
    Comparator for raw facts.

    If the expanded fact A has an intersection with the expanded fact B, then
    this comparator consider they are equal.
    See `fact_expander` and `__eq__` implementation for more details.

    This comparator supports:
    - simple fact notation (i.e. "fact_name")
    - ambiguous fact notation (i.e. "fact_name/other_fact_name")
    - parent from nested facts (i.e. "fact_name__some_nested_key")

    Note:
    Distinct "child" facts coming from the same "parent" (i.e.
    "system_purpose_json__addons" and "system_purpose_json__usage") are considered
    equal as they are coming from the fact.
    """

    def __init__(self, fact_name):
        """Initialize class."""
        self._fact = fact_name
        self._vals = fact_expander(self._fact)

    def _raise_unsupported_object(self, object):
        raise TypeError(
            f"'{object}' is unsupported comparison with facts "
            f"(type={type(object).__name__})"
        )

    def __eq__(self, other):
        """Operator for ==."""
        if isinstance(other, str):
            return self.__class__(other) == self._vals
        if isinstance(other, set):
            return other & self._vals != set()
        if isinstance(other, self.__class__):
            return other._vals == self
        self._raise_unsupported_object(other)

    def __contains__(self, other):
        """Operator for 'in'."""
        if isinstance(other, str):
            other_set = {other}
        elif isinstance(other, set):
            other_set = other
        elif isinstance(other, self.__class__):
            other_set = other._vals
        else:
            self._raise_unsupported_object(other)
        return bool(other_set & self._vals)

    def __str__(self):
        """Dunder str."""
        return self._fact

    def __repr__(self):
        """Dunder repr."""
        return f"<{self.__class__.__name__} {self._fact}>"
