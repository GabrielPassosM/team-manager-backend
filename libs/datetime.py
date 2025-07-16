import calendar
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

from libs.base_types.interval import Interval


def utcnow():
    return datetime.now(timezone.utc)


def brasilia_now():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def this_day_next_month(reference_date: date | None = None) -> date:
    if not reference_date:
        reference_date = brasilia_now().date()

    year = reference_date.year
    month = reference_date.month + 1
    if month > 12:
        month = 1
        year += 1

    day = reference_date.day
    last_day_of_next_month = calendar.monthrange(year, month)[1]
    day = min(day, last_day_of_next_month)

    return date(year, month, day)


def current_month_range(reference_date: date | None = None) -> Interval:
    if not reference_date:
        reference_date = brasilia_now().date()

    first_day = reference_date.replace(day=1)
    last_day = reference_date.replace(
        day=calendar.monthrange(reference_date.year, reference_date.month)[1]
    )

    return Interval(start=first_day, end=last_day)
