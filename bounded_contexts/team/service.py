import random
import string

from loguru import logger

from api.htmls.intention_email import HTML_INTENTION_EMAIL
from bounded_contexts.team.exceptions import (
    TeamNotFound,
    CantEditSomeDemoTeamAttributes,
)
from bounded_contexts.team.models import Team
from bounded_contexts.team.repo import (
    TeamWriteRepo,
    TeamReadRepo,
    IntentionToSubscribeWriteRepo,
    IntentionToSubscribeReadRepo,
)
from bounded_contexts.team.schemas import (
    TeamCreate,
    TeamUpdate,
    IntentionToSubscribeCreate,
)

from uuid import UUID
from sqlmodel import Session

from bounded_contexts.user.exceptions import EmailAlreadyInUse
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from core.consts import DEMO_TEAM_NAME
from core.services.email import send_email
from core.settings import ENV_CONFIG


def create_team(team_data: TeamCreate, session: Session) -> Team:
    codes_used = list(TeamReadRepo(session=session).get_all_codes())
    new_code = team_code_generator(codes_used)
    return TeamWriteRepo(session=session).create(team_data, new_code)


def get_team_by_id(team_id: UUID, session: Session) -> Team:
    team = TeamReadRepo(session=session).get_by_id(team_id)
    if not team:
        raise TeamNotFound()

    return team


def update_team(current_user: User, team_data: TeamUpdate, session: Session) -> Team:
    team = TeamReadRepo(session=session).get_by_id(current_user.team_id)
    if not team:
        raise TeamNotFound()

    if all(
        [
            team.name == team_data.name,
            team.emblem_url == team_data.emblem_url,
            team.foundation_date == team_data.foundation_date,
            team.season_start_date == team_data.season_start_date,
            team.season_end_date == team_data.season_end_date,
            team.primary_color == team_data.primary_color,
        ]
    ):
        return team

    if team.name == DEMO_TEAM_NAME and not current_user.is_super_admin:
        if any(
            [
                team.name != team_data.name,
                team.emblem_url != team_data.emblem_url,
                team.foundation_date != team_data.foundation_date,
            ]
        ):
            raise CantEditSomeDemoTeamAttributes()

    updated_team = TeamWriteRepo(session=session).update(
        team, team_data, current_user.id
    )

    return updated_team


def delete_team(team_id: UUID, session: Session) -> None:
    team = TeamReadRepo(session=session).get_by_id(team_id)
    if not team:
        raise TeamNotFound

    TeamWriteRepo(session=session).delete(team)


def create_intention_to_subscribe(
    intention_data: IntentionToSubscribeCreate, session: Session
) -> None:
    if IntentionToSubscribeReadRepo(session).get_by_email(
        intention_data.user_email
    ) or UserReadRepo(session).get_by_email(intention_data.user_email):
        raise EmailAlreadyInUse()

    IntentionToSubscribeWriteRepo(session).create(intention_data)

    if ENV_CONFIG != "production":
        return

    html_content = (
        HTML_INTENTION_EMAIL.replace("user_name", intention_data.user_name)
        .replace("user_email", intention_data.user_email)
        .replace("phone_number", intention_data.phone_number)
        .replace("team_name", intention_data.team_name)
    )

    try:
        send_email(subject="NOVO CLIENTE !!", html=html_content)
    except Exception as e:
        logger.exception(f"Error sending intention to subscribe email: {e}")


def team_code_generator(codes_used: list[str], length=6) -> str:
    characters = string.ascii_uppercase + string.digits

    while True:
        code = "".join(random.choice(characters) for _ in range(length))
        if code not in codes_used:
            return code
