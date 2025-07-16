from datetime import date

import pytest

from libs.base_types.interval import Interval
from libs.datetime import this_day_next_month, current_month_range


@pytest.mark.parametrize(
    "entry_date, expected_date",
    [
        (date(2025, 5, 21), date(2025, 6, 21)),
        (date(2025, 12, 10), date(2026, 1, 10)),
        (date(2025, 5, 31), date(2025, 6, 30)),
        (date(2025, 1, 31), date(2025, 2, 28)),
        (date(2024, 1, 31), date(2024, 2, 29)),
        (date(2024, 8, 31), date(2024, 9, 30)),
        (date(2024, 10, 31), date(2024, 11, 30)),
    ],
)
def test_this_day_next_month(entry_date, expected_date):
    assert this_day_next_month(entry_date) == expected_date


@pytest.mark.parametrize(
    "entry_date, expected_start, expected_end",
    [
        (date(2025, 5, 21), date(2025, 5, 1), date(2025, 5, 31)),
        (date(2025, 12, 10), date(2025, 12, 1), date(2025, 12, 31)),
        (date(2025, 2, 28), date(2025, 2, 1), date(2025, 2, 28)),
        (date(2024, 2, 29), date(2024, 2, 1), date(2024, 2, 29)),
    ],
)
def test_current_month_range(entry_date, expected_start, expected_end):
    interval = current_month_range(entry_date)
    assert isinstance(interval, Interval)
    assert interval.start == expected_start
    assert interval.end == expected_end
