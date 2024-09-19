"""Test fingerprint formatters."""

import datetime as dt

import pytest

from fingerprinter import formatters


@pytest.mark.parametrize(
    "value,expected_value,formatter",
    (
        ("text", "text", formatters.str_or_none),
        (" text  ", "text", formatters.str_or_none),
        ("", None, formatters.str_or_none),
        ("  ", None, formatters.str_or_none),
        (1, 1, formatters.int_or_none),
        ("1", 1, formatters.int_or_none),
        ("1.1", 1, formatters.int_or_none),
        ("1.1 ", 1, formatters.int_or_none),
        ("some text", None, formatters.int_or_none),
        ("some text", None, formatters.float_or_none),
        ("1.1 ", 1.1, formatters.float_or_none),
        ("1999-01-01", None, formatters.date_or_none),
        pytest.param(
            dt.date.fromisoformat("1999-01-01"),
            dt.date(1999, 1, 1),
            formatters.date_or_none,
            id="date-obj",
        ),
        pytest.param(
            dt.datetime.fromisoformat("1999-01-01T00:00:00"),
            dt.date(1999, 1, 1),
            formatters.date_or_none,
            id="datetime-obj",
        ),
    ),
)
def test_formatter(value, expected_value, formatter):
    """Test formatters."""
    assert formatter(value) == expected_value
