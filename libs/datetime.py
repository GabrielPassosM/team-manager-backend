from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo


def utcnow():
    return datetime.now(timezone.utc)


def brasilia_now():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def this_day_next_month(reference_date: date | None = None) -> date:
    if not reference_date:
        reference_date = date.today()

    year = reference_date.year
    month = reference_date.month
    day = reference_date.day

    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
