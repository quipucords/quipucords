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


def test_average_date_very_large_list_delta():
    """
    Test average_date with a list of dates with a very large date delta.

    This special test case exists because an earlier implementation of
    average_date tried to add timedelta objects, but with a list of dates
    having a sufficiently large delta from the oldest date, we could
    exceed Python timedelta's limit of 999999999 days. The data in this
    test is defined deliberately to exceed >999999999 total days in the
    calculations to confirm that we no longer raise an OverflowError.
    If you invoke a debugger and step through average_date while running
    this test, you should find sum_delta_since_oldest = 1004470089 which
    is greater than the previously encountered 999999999 limit.
    """
    input_dates = [date(2025, 1, 1) for _ in range(50000)]
    input_dates.append(date(1970, 1, 1))
    expected_average = date(2024, 12, 31)
    assert average_date(input_dates) == expected_average
