import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, model_validator, field_validator

from bounded_contexts.championship.schemas import ChampionshipResponse
from bounded_contexts.user.schemas import UserResponse
from core.consts import DEFAULT_PRIMARY_COLOR
from core.schemas import BaseSchema


class _TeamBase(BaseModel):
    name: str
    emblem_url: str | None = None
    foundation_date: date | None = None
    season_start_date: date | None = None
    season_end_date: date | None = None
    primary_color: str | None = DEFAULT_PRIMARY_COLOR

    @model_validator(mode="after")
    def check_season_dates(self):
        if self.season_start_date and self.season_end_date:
            if self.season_end_date <= self.season_start_date:
                raise ValueError("season_end_date must be later than season_start_date")
        return self

    @field_validator("primary_color")
    @classmethod
    def validate_hex_color(cls, v):
        if v is None:
            return v
        if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            raise ValueError("primary_color must be a valid hex color code")
        return v


class TeamCreate(_TeamBase):
    paid_until: date | None = None


class TeamUpdate(_TeamBase):
    pass


class CurrentTeamResponse(BaseSchema, _TeamBase):
    paid_until: date
    code: str | None


class TeamRegister(BaseModel):
    """
    /admin
    """

    # Email saved on IntentionToSubscribe
    user_email: str


class IntentionToSubscribeCreate(BaseModel):
    user_name: str
    user_email: str
    phone_number: str
    team_name: str


class RegisterTeamResponse(BaseModel):
    """
    /admin/register-team
    """

    team: CurrentTeamResponse
    super_user: UserResponse
    client_user: UserResponse
    friendly_championship: ChampionshipResponse
    before_system_championship: ChampionshipResponse


class RenewSubscriptionIn(BaseModel):
    """
    /admin/renew-subscription
    """

    team_ids: list[UUID]
    months: int

    @field_validator("months")
    @classmethod
    def validate_months(cls, v):
        if v < 1 or v > 12:
            raise ValueError("months must be between 1 and 12")
        return v


class RenewSubscriptionResponse(BaseModel):
    renewed_info: dict[date, list[str]]
