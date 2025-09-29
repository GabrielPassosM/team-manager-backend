from uuid import UUID

from sqlmodel import Session

from bounded_contexts.championship.exceptions import (
    ChampionshipAlreadyExists,
    ChampionshipNotFound,
    CantEditFriendlyChampionship,
    CantDeleteFriendlyChampionship,
    CantDeleteChampionshipWithGames,
    CanOnlyEditEndDateBeforeSystemChampionship,
    CantDeleteBeforeSystemChampionship,
)
from bounded_contexts.championship.models import Championship
from bounded_contexts.championship.repo import (
    ChampionshipReadRepo,
    ChampionshipWriteRepo,
)
from bounded_contexts.championship.schemas import (
    ChampionshipCreate,
    ChampionshipUpdate,
    ChampionshipFilter,
)
from bounded_contexts.game_and_stats.game.repo import GameReadRepo
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME, BEFORE_SYSTEM_CHAMPIONSHIP_NAME


def create_championship(
    create_data: ChampionshipCreate, current_user: User, session: Session
) -> Championship:
    if not TeamReadRepo(session=session).get_by_id(current_user.team_id):
        raise TeamNotFound()

    if ChampionshipReadRepo(session=session).get_by_name(
        create_data.name, current_user.team_id
    ):
        raise ChampionshipAlreadyExists()

    return ChampionshipWriteRepo(session=session).create(
        create_data, current_user.team_id, current_user.id
    )


def get_championships_by_team(team_id: UUID, session: Session) -> list[Championship]:
    return ChampionshipReadRepo(session=session).get_all_order_by_status_and_start_date(
        team_id
    )


def filter_championships(
    team_id: UUID, filter_data: ChampionshipFilter, session: Session
) -> list[Championship]:
    return ChampionshipReadRepo(session=session).get_by_filters(team_id, filter_data)


def update_championship(
    champ_id: UUID,
    update_data: ChampionshipUpdate,
    session: Session,
    current_user: User,
) -> Championship:
    champ_to_update = ChampionshipReadRepo(session=session).get_by_id(champ_id)
    if not champ_to_update:
        raise ChampionshipNotFound()

    if champ_to_update.name == FRIENDLY_CHAMPIONSHIP_NAME:
        raise CantEditFriendlyChampionship()

    if ChampionshipUpdate.model_validate(champ_to_update) == update_data:
        return champ_to_update

    if (
        champ_to_update.name == BEFORE_SYSTEM_CHAMPIONSHIP_NAME
        and _changed_any_field_but_one(champ_to_update, update_data, "end_date")
    ):
        raise CanOnlyEditEndDateBeforeSystemChampionship()

    if champ_to_update.name != update_data.name and ChampionshipReadRepo(
        session=session
    ).get_by_name(update_data.name, current_user.team_id):
        raise ChampionshipAlreadyExists()

    return ChampionshipWriteRepo(session=session).update(
        champ_to_update, update_data, current_user.id
    )


def _changed_any_field_but_one(
    champ: Championship, update_data: ChampionshipUpdate, field_name: str
) -> bool:
    champ_data = ChampionshipUpdate.model_validate(champ).model_dump()
    update_data_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_data_dict.items():
        if key != field_name and champ_data.get(key) != value:
            return True
    return False


def delete_championship(champ_id: UUID, current_user: User, session: Session) -> None:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    champ_to_delete = ChampionshipReadRepo(session=session).get_by_id(champ_id)
    if not champ_to_delete:
        raise ChampionshipNotFound()

    if champ_to_delete.name == FRIENDLY_CHAMPIONSHIP_NAME:
        raise CantDeleteFriendlyChampionship()

    if champ_to_delete.name == BEFORE_SYSTEM_CHAMPIONSHIP_NAME:
        raise CantDeleteBeforeSystemChampionship()

    games_count = GameReadRepo(session).count_games_by_championship(champ_id)
    if games_count:
        raise CantDeleteChampionshipWithGames(games_count)

    ChampionshipWriteRepo(session=session).delete(champ_to_delete, current_user.id)
