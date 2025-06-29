from datetime import date, datetime


class Interval:

    class InvalidInterval(ValueError):
        pass

    class EndDateBeforeStart(ValueError):
        pass

    class InvalidDateType(TypeError):
        pass

    def __init__(
        self,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
        treat_as_date: bool = True,
    ):
        if not start and not end:
            raise self.InvalidInterval("At least one of start or end must be provided.")
        if start and end and type(start) != type(end):
            raise self.InvalidDateType("Start and end must be of the same type.")
        if start and end and start > end:
            raise self.EndDateBeforeStart("End date cannot be before start date.")

        if treat_as_date:
            if start:
                start = start.date() if isinstance(start, datetime) else start
            if end:
                end = end.date() if isinstance(end, datetime) else end

        self.start = start
        self.end = end

    @property
    def start_or_end(self) -> date | datetime:
        return self.start or self.end

    def date_is_in_interval(self, date_to_check: date | datetime) -> bool:
        if type(date_to_check) != type(self.start_or_end):
            raise self.InvalidDateType(
                f"Date to check must the same type as the interval dates. ({type(self.start_or_end)})"
            )

        if self.start and self.end:
            return self.start <= date_to_check <= self.end
        if self.start:
            return self.start <= date_to_check
        if self.end:
            return date_to_check <= self.end
        return False
