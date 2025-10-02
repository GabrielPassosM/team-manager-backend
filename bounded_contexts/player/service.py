from uuid import UUID

from loguru import logger
from sqlmodel import Session

from bounded_contexts.game_and_stats.game.service import (
    create_before_system_game_and_stats,
)
from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.player.exceptions import PlayerNotFound, PlayersLimitReached
from bounded_contexts.player.models import Player
from bounded_contexts.player.repo import PlayerReadRepo, PlayerWriteRepo
from bounded_contexts.player.schemas import (
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerNameAndShirt,
    PlayerResponse,
    PlayersStatsFilter,
)
from bounded_contexts.storage.service import delete_player_image_from_bucket
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserWriteRepo
from core.exceptions import AdminRequired
from core.schemas import StatsSchema


def create_player(
    create_data: PlayerCreate, current_user: User, session: Session
) -> Player:
    # Non admins can create only one player for themselves
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

    stats = StatsSchema(**create_data.model_dump())
    if _has_any_stats(stats) and current_user.has_admin_privileges:
        try:
            create_before_system_game_and_stats(player.id, stats, current_user, session)
            player.has_before_system_stats = True
            PlayerWriteRepo(session).save(player, current_user.id)
        except Exception as e:
            logger.exception(f"Error creating before system stats: {e}")

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


def update_player(
    player_id: UUID, update_data: PlayerUpdate, session: Session, current_user: User
) -> PlayerResponse:
    if not current_user.has_admin_privileges and current_user.player_id != player_id:
        raise AdminRequired()

    player_to_update = PlayerReadRepo(session=session).get_by_id(player_id)
    if not player_to_update:
        raise PlayerNotFound()

    if PlayerUpdate.model_validate(player_to_update) == update_data:
        return player_to_update

    stats = StatsSchema(**update_data.model_dump())
    if (
        _has_any_stats(stats)
        and current_user.has_admin_privileges
        and not player_to_update.has_before_system_stats
    ):
        try:
            create_before_system_game_and_stats(
                player_to_update.id, stats, current_user, session
            )
            player_to_update.has_before_system_stats = True
            PlayerWriteRepo(session).save(player_to_update, current_user.id)
        except Exception as e:
            logger.exception(f"Error creating before system stats: {e}")

    player_updated = PlayerWriteRepo(session=session).update(
        player_to_update, update_data, current_user.id
    )
    return _make_player_response(player_updated)


def _has_any_stats(stats_data: StatsSchema) -> bool:
    return any(
        [
            stats_data.played > 0,
            stats_data.goals > 0,
            stats_data.assists > 0,
            stats_data.yellow_cards > 0,
            stats_data.red_cards > 0,
            stats_data.mvps > 0,
        ]
    )


def _make_player_response(player: Player) -> PlayerResponse:
    played, goals, assists, yellows, reds, mvps = 0, 0, 0, 0, 0, 0

    for stat in player.game_player_stat:
        if stat.stat == StatOptions.PLAYED:
            played += stat.quantity
        elif stat.stat == StatOptions.GOAL:
            goals += stat.quantity
        elif stat.stat == StatOptions.ASSIST:
            assists += stat.quantity
        elif stat.stat == StatOptions.YELLOW_CARD:
            yellows += stat.quantity
        elif stat.stat == StatOptions.RED_CARD:
            reds += stat.quantity
        elif stat.stat == StatOptions.MVP:
            mvps += stat.quantity

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
        has_before_system_stats=player.has_before_system_stats,
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


def get_players_filtered_by_stats(
    filter_data: PlayersStatsFilter, team_id: UUID, session: Session
) -> list[PlayerResponse]:
    return PlayerReadRepo(session).get_players_filtered_by_stats(filter_data, team_id)
