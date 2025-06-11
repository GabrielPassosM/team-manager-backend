from uuid import UUID

from sqlmodel import Session

from bounded_contexts.player.exceptions import PlayerNotFound
from bounded_contexts.player.models import Player
from bounded_contexts.player.repo import PlayerReadRepo, PlayerWriteRepo
from bounded_contexts.player.schemas import PlayerCreate, PlayerUpdate, PlayerFilter
from bounded_contexts.storage.service import delete_player_image_from_bucket
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User


def create_player(
    create_data: PlayerCreate, current_user: User, session: Session
) -> Player:
    if not TeamReadRepo(session=session).get_by_id(current_user.team_id):
        raise TeamNotFound()

    return PlayerWriteRepo(session=session).save(
        create_data, current_user.team_id, current_user.id
    )


def get_players_by_team(team_id: UUID, session: Session) -> list[Player]:
    return PlayerReadRepo(session=session).get_all(team_id)


def update_player(
    player_id: UUID, update_data: PlayerUpdate, session: Session, current_user_id: UUID
) -> Player:
    player_to_update = PlayerReadRepo(session=session).get_by_id(player_id)
    if not player_to_update:
        raise PlayerNotFound()

    if PlayerUpdate.model_validate(player_to_update) == update_data:
        return player_to_update

    return PlayerWriteRepo(session=session).update(
        player_to_update, update_data, current_user_id
    )


def delete_player(player_id: UUID, session: Session, current_user_id: UUID) -> None:
    player_to_delete = PlayerReadRepo(session=session).get_by_id(player_id)
    if not player_to_delete:
        raise PlayerNotFound()

    if player_to_delete.image_url:
        delete_player_image_from_bucket(player_to_delete.image_url)

    PlayerWriteRepo(session=session).delete(player_to_delete, current_user_id)


def filter_players(
    team_id: UUID, filter_data: PlayerFilter, session: Session
) -> list[Player]:
    return PlayerReadRepo(session=session).get_by_filters(team_id, filter_data)


def get_players_without_user(team_id: UUID, session: Session) -> list[Player]:
    return PlayerReadRepo(session=session).get_all_without_user(team_id)
