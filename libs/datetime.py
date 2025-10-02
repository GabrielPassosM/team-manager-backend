import calendar
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo

from libs.base_types.interval import Interval


UTC = timezone.utc
BRT = timezone(timedelta(hours=-3))


def utcnow():
    return datetime.now(UTC)


def brasilia_now():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def add_or_subtract_months_to_date(
    reference_date: date | None = None, months: int = 1
) -> date:
    """
    Return the resulting date after adding or subtracting a number of months to/from the reference date.

    MUST NOT CHANGE THE DEFAULT VALUE OF MONTHS - used as default factory in Team.paid_until

    :param reference_date: Base date for calculation. If None, we use the current date in Brasília timezone.
    :param months: Number of months to add (positive) or subtract (negative).
    :return: New date after adjusting by the given number of months.
    """

    if not reference_date:
        reference_date = brasilia_now().date()

    year = reference_date.year + (reference_date.month - 1 + months) // 12
    month = (reference_date.month - 1 + months) % 12 + 1

    day = reference_date.day
    last_day_of_target_month = calendar.monthrange(year, month)[1]
    day = min(day, last_day_of_target_month)

    return date(year, month, day)


def current_month_range(reference_date: date | None = None) -> Interval:
    if not reference_date:
        reference_date = brasilia_now().date()

    first_day = reference_date.replace(day=1)
    last_day = reference_date.replace(
        day=calendar.monthrange(reference_date.year, reference_date.month)[1]
    )

    return Interval(start=first_day, end=last_day)


def date_to_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)
