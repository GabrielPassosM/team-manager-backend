from datetime import date

import pytest

from libs.datetime import this_day_next_month


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
