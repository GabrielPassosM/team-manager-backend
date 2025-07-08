from uuid import UUID

from sqlmodel import Session

from bounded_contexts.game_and_stats.availability.repo import (
    AvailabilityWriteRepo,
    AvailabilityReadRepo,
)
from bounded_contexts.game_and_stats.availability.schemas import (
    GamePlayerAvailabilityCreate,
    GamePlayersAvailabilityResponse,
    GamePlayerAvailabilityUpdate,
)
from bounded_contexts.game_and_stats.exceptions import (
    GameNotFound,
    UserNeedsAssociatedPlayer,
    AvailabilityNotFound,
)
from bounded_contexts.game_and_stats.game.repo import GameReadRepo
from bounded_contexts.game_and_stats.models import AvailabilityStatus
from bounded_contexts.user.models import User


def create_game_player_availability(
    create_data: GamePlayerAvailabilityCreate, session: Session, current_user: User
) -> None:
    user_player = current_user.player
    if not user_player:
        raise UserNeedsAssociatedPlayer(is_admin=current_user.has_admin_privileges)

    game = GameReadRepo(session).get_by_id(create_data.game_id)
    if not game:
        raise GameNotFound()

    deleted_availability = AvailabilityReadRepo(session).get_by_game_and_player(
        game_id=create_data.game_id, player_id=user_player.id, deleted=True
    )

    if deleted_availability:
        AvailabilityWriteRepo(session).reactivate(
            availability=deleted_availability,
            new_status=create_data.status,
            current_user_id=current_user.id,
        )
    else:
        AvailabilityWriteRepo(session).create(
            create_data=create_data,
            team_id=current_user.team_id,
            player_id=user_player.id,
            current_user_id=current_user.id,
        )


def get_game_players_availability(
    game_id: UUID, session: Session, current_user: User
) -> GamePlayersAvailabilityResponse:
    if not GameReadRepo(session).get_by_id(game_id):
        raise GameNotFound()

    availabilities = AvailabilityReadRepo(session).get_by_game_id(game_id)

    user_player = current_user.player

    available, not_available, doubt = [], [], []
    user_player_availability = None
    user_player_name = None
    for availability in availabilities:
        player = availability.player

        if user_player and player.id == user_player.id:
            user_player_availability = availability.status
            user_player_name = player.name
            continue

        if availability.status == AvailabilityStatus.AVAILABLE:
            available.append(player.name)
        elif availability.status == AvailabilityStatus.NOT_AVAILABLE:
            not_available.append(player.name)
        elif availability.status == AvailabilityStatus.DOUBT:
            doubt.append(player.name)

    if user_player_availability and user_player_name:
        if user_player_availability == AvailabilityStatus.AVAILABLE:
            available.insert(0, user_player_name)
        elif user_player_availability == AvailabilityStatus.NOT_AVAILABLE:
            not_available.insert(0, user_player_name)
        elif user_player_availability == AvailabilityStatus.DOUBT:
            doubt.insert(0, user_player_name)

    return GamePlayersAvailabilityResponse(
        current_player=user_player_availability,
        available=available,
        not_available=not_available,
        doubt=doubt,
    )


def update_game_player_availability(
    update_data: GamePlayerAvailabilityUpdate,
    game_id: UUID,
    session: Session,
    current_user: User,
) -> None:
    user_player = current_user.player
    if not user_player:
        raise UserNeedsAssociatedPlayer(is_admin=current_user.has_admin_privileges)

    availability = AvailabilityReadRepo(session).get_by_game_and_player(
        game_id=game_id, player_id=user_player.id
    )
    if not availability:
        raise AvailabilityNotFound()

    AvailabilityWriteRepo(session).update(
        availability=availability,
        update_data=update_data,
        current_user_id=current_user.id,
    )


def delete_game_player_availability(
    game_id: UUID, session: Session, current_user: User
) -> None:
    user_player = current_user.player
    if not user_player:
        raise UserNeedsAssociatedPlayer(is_admin=current_user.has_admin_privileges)

    availability = AvailabilityReadRepo(session).get_by_game_and_player(
        game_id=game_id, player_id=user_player.id
    )
    if not availability:
        raise AvailabilityNotFound()

    AvailabilityWriteRepo(session).delete(
        availability=availability,
        current_user_id=current_user.id,
    )


def delete_game_players_availability(
    game_id: UUID, current_user_id: UUID, session: Session
) -> None:
    availabilities = AvailabilityReadRepo(session).get_by_game_id(game_id)
    if not availabilities:
        return

    AvailabilityWriteRepo(session).delete_many_without_commit(
        availabilities, current_user_id
    )
