"""Tests for `utils.sanitize_for_utf8_compatibility`."""

import pytest

from utils import sanitize_for_utf8_compatibility


@pytest.mark.parametrize(
    "original,expected",
    [
        ("potato", "potato"),
        ("potato\udcc0", "potato?"),
        ("πø†åTØ🥔", "πø†åTØ🥔"),  # non-ASCII UTF-8 characters are okay
        (["a", "b\udcc0"], ["a", "b?"]),
        ({"a": "A\udcc0", "b\udcc0": "B"}, {"a": "A?", "b?": "B"}),
        ({"a": ["A\udcc0"], "b\udcc0": "B"}, {"a": ["A?"], "b?": "B"}),
        (("a", "b\udcc0"), ("a", "b?")),
        (b"\udcc0", b"\udcc0"),  # we do not change raw bytes objects
        (None, None),
    ],
)
def test_sanitize_for_utf8_compatibility(original, expected):
    """Test values are santized for utf-8 compatibility."""
    assert sanitize_for_utf8_compatibility(original) == expected
