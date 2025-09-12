import calendar
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

from libs.base_types.interval import Interval


def utcnow():
    return datetime.now(timezone.utc)


def brasilia_now():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def add_months_to_date(reference_date: date | None = None, months: int = 1) -> date:
    """
    Return de resulting date after adding a number of months to the reference date.

    MUST NOT CHANGE THE DEFAULT VALUE OF MONTHS - used as default factory in Team.paid_until

    :param reference_date: Base data for calculation. If None, we use the current date in Brasília timezone
    :param months: Number of months to add (1-12)
    :return: New date after adding the months
    :raises ValueError: If months is not between 1 and 12
    """
    if months < 1 or months > 12:
        raise ValueError("Months must be between 1 and 12")

    if not reference_date:
        reference_date = brasilia_now().date()

    year = reference_date.year
    month = reference_date.month + months

    year += (month - 1) // 12
    month = ((month - 1) % 12) + 1

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
