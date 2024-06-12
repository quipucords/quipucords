"""Utility functions to help manipulate datetime-related objects."""

from collections.abc import Iterable
from datetime import date, timedelta


def average_date(dates: Iterable[date | None]) -> date | None:
    """Find the average date from an Iterable of date objects."""
    dates = [_date for _date in dates if _date]
    if not dates:
        return None
    oldest = min(dates)
    sum_delta_since_oldest: int = sum(
        ((_date - oldest).days for _date in dates if _date), 0
    )
    average_days_delta = sum_delta_since_oldest / len(dates)
    average = oldest + timedelta(days=average_days_delta)
    return average
