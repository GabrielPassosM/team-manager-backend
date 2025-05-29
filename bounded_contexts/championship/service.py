from uuid import UUID

from sqlmodel import Session

from bounded_contexts.championship.exceptions import (
    ChampionshipAlreadyExists,
    ChampionshipNotFound,
)
from bounded_contexts.championship.models import Championship
from bounded_contexts.championship.repo import (
    ChampionshipReadRepo,
    ChampionshipWriteRepo,
)
from bounded_contexts.championship.schemas import ChampionshipCreate, ChampionshipUpdate
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


def update_championship(
    champ_id: UUID,
    update_data: ChampionshipUpdate,
    session: Session,
    current_user: User,
) -> Championship:
    champ_to_update = ChampionshipReadRepo(session=session).get_by_id(champ_id)
    if not champ_to_update:
        raise ChampionshipNotFound()

    if ChampionshipUpdate.model_validate(champ_to_update) == update_data:
        return champ_to_update

    if champ_to_update.name != update_data.name and ChampionshipReadRepo(
        session=session
    ).get_by_name(update_data.name, current_user.team_id):
        raise ChampionshipAlreadyExists()

    return ChampionshipWriteRepo(session=session).update(
        champ_to_update, update_data, current_user.id
    )


def delete_championship(champ_id: UUID, current_user: User, session: Session) -> None:
    champ_to_delete = ChampionshipReadRepo(session=session).get_by_id(champ_id)
    if not champ_to_delete:
        raise ChampionshipNotFound()

    ChampionshipWriteRepo(session=session).delete(champ_to_delete, current_user.id)
