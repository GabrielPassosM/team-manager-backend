from uuid import UUID

from sqlmodel import Session

from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.game_and_stats.stats.service import delete_player_stats
from bounded_contexts.player.exceptions import PlayerNotFound, PlayersLimitReached
from bounded_contexts.player.models import Player
from bounded_contexts.player.repo import PlayerReadRepo, PlayerWriteRepo
from bounded_contexts.player.schemas import (
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerNameAndShirt,
    PlayerResponse,
)
from bounded_contexts.storage.service import delete_player_image_from_bucket
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserWriteRepo
from core.exceptions import AdminRequired


def create_player(
    create_data: PlayerCreate, current_user: User, session: Session
) -> Player:
    if not current_user.has_admin_privileges and current_user.player_id:
        raise AdminRequired()

    team_id = current_user.team_id
    team = TeamReadRepo(session=session).get_by_id(team_id)
    if not team:
        raise TeamNotFound()

    team_players_count = PlayerReadRepo(session=session).count_by_team_id(team_id)
    if team_players_count >= team.max_players_or_users:
        raise PlayersLimitReached()

    player = PlayerWriteRepo(session=session).create(
        create_data, current_user.team_id, current_user.id
    )
    if not current_user.has_admin_privileges:
        current_user.player_id = player.id
        UserWriteRepo(session).save(current_user, current_user.id)

    return player


def get_players_and_stats(
    team_id: UUID, session: Session, current_player_id: UUID | None = None
) -> list[PlayerResponse]:
    players = PlayerReadRepo(session=session).get_by_team_id(team_id)

    response_items = []
    current_player_item = None
    for player in players:
        item = _make_player_response(player)
        if current_player_id and player.id == current_player_id:
            current_player_item = item
            continue

        response_items.append(item)

    if current_player_item:
        response_items.insert(0, current_player_item)

    return response_items


def filter_players(
    team_id: UUID, filter_data: PlayerFilter, session: Session
) -> list[PlayerResponse]:
    players = PlayerReadRepo(session=session).get_by_filters(team_id, filter_data)

    response_items = []
    for player in players:
        response_items.append(_make_player_response(player))

    return response_items


def _make_player_response(player: Player) -> PlayerResponse:
    played, goals, assists, yellows, reds, mvps = 0, 0, 0, 0, 0, 0
    for stat in player.game_player_stat:
        if stat.stat == StatOptions.PLAYED:
            played += 1
        elif stat.stat == StatOptions.GOAL:
            goals += 1
        elif stat.stat == StatOptions.ASSIST:
            assists += 1
        elif stat.stat == StatOptions.YELLOW_CARD:
            yellows += 1
        elif stat.stat == StatOptions.RED_CARD:
            reds += 1
        elif stat.stat == StatOptions.MVP:
            mvps += 1

    return PlayerResponse(
        id=player.id,
        name=player.name,
        image_url=player.image_url,
        shirt_number=player.shirt_number,
        position=player.position,
        played=played,
        goals=goals,
        assists=assists,
        yellow_cards=yellows,
        red_cards=reds,
        mvps=mvps,
    )


def update_player(
    player_id: UUID, update_data: PlayerUpdate, session: Session, current_user: User
) -> Player:
    if not current_user.has_admin_privileges and current_user.player_id != player_id:
        raise AdminRequired()

    player_to_update = PlayerReadRepo(session=session).get_by_id(player_id)
    if not player_to_update:
        raise PlayerNotFound()

    if PlayerUpdate.model_validate(player_to_update) == update_data:
        return player_to_update

    return PlayerWriteRepo(session=session).update(
        player_to_update, update_data, current_user.id
    )


def delete_player(player_id: UUID, session: Session, current_user: User) -> None:
    if not current_user.has_admin_privileges and current_user.player_id != player_id:
        raise AdminRequired()

    player_to_delete = PlayerReadRepo(session=session).get_by_id(player_id)
    if not player_to_delete:
        raise PlayerNotFound()

    if player_to_delete.image_url:
        delete_player_image_from_bucket(player_to_delete.image_url)

    try:
        delete_player_stats(player_id, current_user.id, session)
        if player_to_delete.user:
            UserWriteRepo(session=session).remove_player_without_commit(
                player_to_delete.user, current_user.id
            )
        PlayerWriteRepo(session=session).delete_without_commit(
            player_to_delete, current_user.id
        )
    except Exception as e:
        session.rollback()
        raise e

    session.commit()


def get_players_without_user(team_id: UUID, session: Session) -> list[Player]:
    return PlayerReadRepo(session=session).get_all_without_user(team_id)


def get_all_players_only_name_and_shirt(
    team_id: UUID, session: Session
) -> list[PlayerNameAndShirt]:
    return PlayerReadRepo(session=session).get_all_players_only_name_and_shirt(team_id)
