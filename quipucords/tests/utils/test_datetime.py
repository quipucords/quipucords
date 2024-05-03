"""Test helper utility functions in utils.datetime."""

from datetime import date

import pytest

from utils.datetime import average_date


@pytest.mark.parametrize(
    "input_dates,expected_result",
    (
        ([], None),
        ([None, None], None),
        (
            [date(2024, 4, 1)],
            date(2024, 4, 1),
        ),
        (
            [date(2024, 4, 1), None],
            date(2024, 4, 1),
        ),
        (
            [
                date(2024, 4, 1),
                date(2024, 4, 1),
            ],
            date(2024, 4, 1),
        ),
        (
            [
                date(2024, 3, 31),
                date(2024, 4, 2),
            ],
            date(2024, 4, 1),
        ),
    ),
)
def test_average_date(input_dates, expected_result):
    """Test average_date with various inputs."""
    assert average_date(input_dates) == expected_result
