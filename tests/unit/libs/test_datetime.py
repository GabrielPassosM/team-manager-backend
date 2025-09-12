from datetime import date

import pytest

from libs.base_types.interval import Interval
from libs.datetime import add_months_to_date, current_month_range


@pytest.mark.parametrize(
    "reference_date, months, expected",
    [
        # Simple case within the same year
        (date(2023, 1, 15), 1, date(2023, 2, 15)),
        (date(2023, 5, 10), 3, date(2023, 8, 10)),
        # Next month with less days
        (date(2023, 1, 31), 1, date(2023, 2, 28)),  # (non leap year)
        (date(2020, 1, 31), 1, date(2020, 2, 29)),  # (leap year)
        # Year transition
        (date(2023, 11, 30), 2, date(2024, 1, 30)),
        (date(2023, 12, 15), 1, date(2024, 1, 15)),
        # Max allowed months - 1 year ahead
        (date(2023, 6, 5), 12, date(2024, 6, 5)),
    ],
)
def test_add_months_to_date(reference_date, months, expected):
    assert add_months_to_date(reference_date, months) == expected


@pytest.mark.parametrize("invalid_months", [0, 13, -5, 100])
def test_add_months_invalid(invalid_months):
    with pytest.raises(ValueError):
        add_months_to_date(date(2023, 1, 1), invalid_months)


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
