from uuid import UUID

from sqlmodel import Session

from bounded_contexts.championship.exceptions import ChampionshipAlreadyExists
from bounded_contexts.championship.models import Championship
from bounded_contexts.championship.repo import (
    ChampionshipReadRepo,
    ChampionshipWriteRepo,
)
from bounded_contexts.championship.schemas import ChampionshipCreate
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User


def create_championship(
    create_data: ChampionshipCreate, team_id: UUID, session: Session, current_user: User
) -> Championship:
    if not TeamReadRepo(session=session).get_by_id(team_id):
        raise TeamNotFound()

    if ChampionshipReadRepo(session=session).get_by_name(create_data.name, team_id):
        raise ChampionshipAlreadyExists()

    return ChampionshipWriteRepo(session=session).save(
        create_data, team_id, current_user.id
    )


def get_championships_by_team(team_id: UUID, session: Session) -> list[Championship]:
    return ChampionshipReadRepo(session=session).get_all_order_by_status_and_start_date(
        team_id
    )
