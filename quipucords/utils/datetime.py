"""Utility functions to help manipulate datetime-related objects."""

from collections.abc import Iterable
from datetime import date, timedelta


def average_date(dates: Iterable[date | None]) -> date | None:
    """Find the average date from an Iterable of date objects."""
    dates = [_date for _date in dates if _date]
    if not dates:
        return None
    oldest = min(dates)
    sum_delta_since_oldest = sum(
        (_date - oldest for _date in dates if _date), timedelta()
    )
    average = oldest + sum_delta_since_oldest / len(dates)
    return average
