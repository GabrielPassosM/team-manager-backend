from datetime import date, datetime

from pydantic import BaseModel, model_validator


class NumberRangeSchema(BaseModel):
    min: int | float | None = None
    max: int | float | None = None

    @model_validator(mode="after")
    def check_min_and_max(self):
        if not self.min and not self.max:
            raise ValueError("At least one of min or max must be provided.")

        if not self.min or not self.max:
            return self

        if self.min > self.max:
            raise ValueError("Min cannot be bigger than max.")

        return self


class DateRangeSchema(BaseModel):
    start: date | datetime | None = None
    end: date | datetime | None = None

    @model_validator(mode="after")
    def check_start_and_end(self):
        if not self.start and not self.end:
            raise ValueError("At least one of start or end must be provided.")

        if not self.start or not self.end:
            return self

        if type(self.start) != type(self.end):
            raise ValueError("Start and end must be of the same type.")

        if self.start > self.end:
            raise ValueError("Start cannot be bigger than end.")

        return self
